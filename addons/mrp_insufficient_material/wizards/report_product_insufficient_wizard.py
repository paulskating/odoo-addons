# _*_ coding: utf-8 _*_
import datetime
import StringIO
import base64
import string

from openerp import models, fields, api, _


class ReportProductInsufficientWizard(models.TransientModel):
    _name = "mrp_insufficient_material.report_product_insuf_wizard"

    filter_by = fields.Selection([("date", "Date"),
                                  ("order", "Order"),
                                  ("order_range", "Order Range")], required=True)
    date_to = fields.Date()
    order_ids = fields.Many2many("mrp.production", string="Orders",
                                 relation="mrp_insufficient_material_rpt_product_insuf_mo_rel",
                                 domain=["!", ("state", "in", ("done", "cancel"))])
    order_from = fields.Char()
    order_to = fields.Char()

    take_date = fields.Date()

    location_ids = fields.Many2many("stock.location", string="Stock Locations",
                                    relation="mrp_insufficient_material_rpt_product_insuf_loc_rel")

    product_ids = fields.Many2many("product.product", string="Products",
                                   relation="mrp_insufficient_material_rpt_product_insuf_product_rel",
                                   domain=[('bom_ids', '!=', False), ('bom_ids.type', '!=', 'phantom')],
                                   help="Products the production produce.")

    only_print_insufficient = fields.Boolean()
    allow_print_zero_use = fields.Boolean()

    xls_file = fields.Binary()
    xls_file_name = fields.Char()

    state = fields.Selection([("normal", "Normal"), ("download_xls", "Download xls")],
                             default="normal")

    @api.multi
    def get_data(self):
        self.ensure_one()
        data = {
            "filter_by": self.filter_by,
            "date_to": self.date_to,
            "order_ids": self.order_ids.ids,
            "order_from": self.order_from,
            "order_to": self.order_to,
            "take_date": self.take_date,
            "location_ids": self.location_ids.ids,
            "product_ids": self.product_ids.ids,
            "only_print_insufficient": self.only_print_insufficient,
            "allow_print_zero_use": self.allow_print_zero_use
        }
        return data

    @api.multi
    def action_print(self):
        self.ensure_one()
        data = self.get_data()
        return self.env["report"].get_action(self, "mrp_insufficient_material.report_product_insufficient", data=data)

    @api.multi
    def generate_xls(self):
        self.ensure_one()

        import xlwt
        data = self.get_data()
        report = self.env["report.mrp_insufficient_material.report_product_insufficient"]
        lines = report.get_report_lines(data)

        style0 = xlwt.easyxf('font: name Times New Roman, color-index red, bold on',
                             num_format_str='#,##0.00')
        style1 = xlwt.easyxf(num_format_str='D-MMM-YY')

        wb = xlwt.Workbook()
        ws = wb.add_sheet('A Test Sheet')

        row = 2

        ws.write(row, 6, u"料件缺料狀況表")
        row += 1

        filter_by = data.get("filter_by", None)
        if filter_by == "date":
            date_to = data.get("date_to", None)
            ws.write(row, 0, u"日期截止：%s" % date_to)
        if filter_by == "order_range":
            order_from = data.get("order_from", "")
            order_to = data.get("order_to", "")
            ws.write(row, 0, u"製令單號：%s - %s" % (order_from, order_to))
        if filter_by == "order":
            order_ids = data.get("order_ids", [])
            order_names = ""
            if order_ids:
                order_names = string.join(self.env["mrp.production"].browse(order_ids).mapped("name"), ","),
            ws.write(row, 0, u"製令單號：%s" % order_names)
        date = fields.Date.today()
        ws.write(row, 17, u"製表日期：%s" % date)
        row += 1

        titles = [u"產品編號",
                  u"產品名稱",
                  u"規格",
                  u"現有庫存",
                  u"預計入庫",
                  u"預計領用日",
                  u"預計用量",
                  u"累積用量",
                  u"已發數量",
                  u"庫存結餘",
                  u"製令單號",
                  u"產品名稱",
                  u"訂單編號",
                  u"母製令號",
                  u"領料庫別",
                  u"工藝代碼",
                  u"工藝名稱",
                  u"加工廠商",
                  u"廠商名稱"]
        col = 0
        for title in titles:
            ws.write(row, col, title)
            col += 1
        row += 1

        for line in lines:
            ws.write(row, 0, line.get("product_code", None) or "")
            ws.write(row, 1, line.get("product_name", None) or "")
            ws.write(row, 2, line.get("product_description", None) or "")
            ws.write(row, 3, line.get("qty_in_stock_detail_str", None) or "")
            ws.write(row, 4, line.get("product_incoming_qty", None) or "")
            ws.write(row, 5, line.get("product_planned_take_date", None) or "")
            ws.write(row, 6, line.get("product_need_qty", None) or "")
            ws.write(row, 7, line.get("product_usage", None) or "")
            ws.write(row, 8, line.get("product_qty_put", None) or "")
            ws.write(row, 9, line.get("product_remain_qty", None) or "")
            ws.write(row, 10, line.get("order_name", None) or "")
            ws.write(row, 11, line.get("order_product_name_with_code", None) or "")
            ws.write(row, 12, line.get("order_origin", None) or "")
            ws.write(row, 13, line.get("order_name", None) or "")
            ws.write(row, 14, line.get("product_source_location", None) or "")
            ws.write(row, 15, line.get("order_route_code", None) or "")
            ws.write(row, 16, line.get("order_route_name", None) or "")
            row += 1
        output = StringIO.StringIO()

        wb.save(output)

        self.xls_file = base64.standard_b64encode(output.getvalue())
        self.xls_file_name = _("料件欠料表.xls")

    @api.multi
    def action_download(self):
        self.ensure_one()
        self.generate_xls()
        self.state = "download_xls"
        return {'type': 'ir.actions.act_window',
                'res_model': self._name,
                'res_id': self.id,
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new'}

    @api.multi
    def action_back(self):
        self.ensure_one()
        self.state = "normal"
        return {'type': 'ir.actions.act_window',
                'res_model': self._name,
                'res_id': self.id,
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new'}
