# _*_ coding: utf-8 _*_
from openerp import models, fields, api


class SubcontractLine(models.Model):
    _name = "mrp.subcontract.order.line"

    order_id = fields.Many2one("mrp.subcontract", ondelete='cascade', required=True)
    bom_id = fields.Many2one("mrp.bom", required=True)
    product_id = fields.Many2one("product.product", required=True,
                                 domain=[('bom_ids', '!=', False), ('bom_ids.type', '!=', 'phantom')])
    product_uom_qty = fields.Float(required=True)
    unit_price = fields.Float(required=True)
    product_uom_id = fields.Many2one("product.uom", required=True)
    schedule_date = fields.Date(required=True)
    scheduled_products_ids = fields.One2many("stock.move", "sub_order_line_id", "Scheduled Products")

    @api.multi
    @api.onchange("product_id")
    def _onchange_product_id(self):
        for line in self:
            line.product_uom_id = line.product_id.uom_id

    @api.multi
    def explode_bom(self):
        Bom = self.env["mrp.bom"]
        StockMove = self.env["stock.move"]
        for sub_line in self:
            if sub_line.bom_id:
                product_detail, work_center_detail = Bom._bom_explode(bom=self.bom_id, product=False,
                                                                      factor=self.product_uom_qty)
                for detail_line in product_detail:
                    vals = dict()
                    vals["name"] = detail_line["name"]
                    vals["product_id"] = detail_line["product_id"]
                    vals["from_bom_product_id"] = detail_line["product_id"]
                    vals["sub_order_id"] = sub_line.order_id.id
                    vals["sub_order_line_id"] = sub_line.id
                    vals["product_uom_qty"] = detail_line["product_qty"]
                    vals["product_uom"] = detail_line["product_uom"]
                    vals["date_expected"] = sub_line.schedule_date
                    vals["location_id"] = sub_line.order_id.location_src_id.id
                    vals["location_dest_id"] = sub_line.order_id.location_partner_production_id.id

                    StockMove.create(vals)
                if sub_line.scheduled_products_ids:
                    sub_line.scheduled_products_ids.action_confirm()
        return True
