# _*_ coding: utf-8 _*_
import datetime
import string
from collections import defaultdict
from itertools import groupby

from openerp import models, fields, api


class ReportProductInsufficient(models.AbstractModel):
    _name = 'report.mrp_insufficient_material.report_product_insufficient'

    def get_domain(self, data=None):
        if not data:
            return None

        domain = ["!", ("state", "in", ("done", "cancel"))]

        filter_by = data.get("filter_by", None)
        date_to = data.get("date_to", None)
        order_from = data.get("order_from", None)
        order_to = data.get("order_to", None)
        order_ids = data.get("order_ids", None)

        if filter_by == "date" and date_to:
            today = fields.Date.today()
            domain.append(("date_planned", ">=", today))
            domain.append(("date_planned", "<=", date_to))
        elif filter_by == "order" and order_ids:
            domain.append(("id", "in", order_ids))
        elif filter_by == "order_range" and all((order_from, order_to)):
            domain.append(("name", ">=", order_from))
            domain.append(("name", "<=", order_to))

        product_ids = data.get("product_ids", None)
        if product_ids:
            domain.append(("product_id", "in", product_ids))

        location_ids = data.get("location_ids", None)
        if location_ids:
            domain.append(("location_src_id", "in", location_ids))

        return domain

    @api.multi
    def render_html(self, data=None):
        lines = self.get_report_lines(data)

        docargs = {
            "date": fields.Date.today(),
            "lines": lines,
            "filter_by": data.get("filter_by", None),
            "date_to": data.get("date_to", None),
            "order_from": data.get("order_from", None),
            "order_to": data.get("order_to", None),
            "order_names": string.join(self.env["mrp.production"].browse(data.get("order_ids", [])).mapped("name"),
                                       ","),
            "product_names": string.join(self.env["product.product"].browse(data.get("product_ids", [])).mapped("name"),
                                         ",")
        }
        return self.env['report'].render('mrp_insufficient_material.report_product_insufficient_template',
                                         values=docargs)

    def get_report_lines(self, data):
        Production = self.env["mrp.production"]
        StockMove = self.env["stock.move"]
        location_suppliers = self.env.ref("stock.stock_location_suppliers")
        domain = self.get_domain(data)
        take_date = data.get("take_date", None)
        only_print_insufficient = data.get("only_print_insufficient", None)
        allow_print_zero_use = data.get("allow_print_zero_use", None)
        orders = Production.search(domain)
        # all_moves = reduce(lambda x, y: x.move_lines + y.move_lines, orders)
        lines = list()
        product_usage = defaultdict(lambda: 0)
        product_incoming_moves = dict()
        for order in orders:
            str_product_planned_take_date = take_date
            if not str_product_planned_take_date:
                dt_planned_date = fields.Date.from_string(take_date or order.date_planned)
                dt_product_planned_take_date = dt_planned_date + datetime.timedelta(days=-7)
                str_product_planned_take_date = fields.Date.to_string(dt_product_planned_take_date)

            grouped_move_lines = groupby(order.move_lines, lambda move: move.product_id)
            for product_id, moves in grouped_move_lines:
                moves = list(moves)
                line = dict()

                reserved_qty = sum(q.qty for move in moves for q in move.reserved_quant_ids)
                total_qty = sum(move.product_uom_qty for move in moves)
                need_qty = total_qty - reserved_qty
                if not allow_print_zero_use and need_qty <= 0:
                    continue

                qty_available = product_id.qty_in_stock
                product_usage[product_id.id] += need_qty
                remain_qty = qty_available - product_usage[product_id.id]
                if only_print_insufficient and remain_qty >= 0:
                    continue

                qty_in_stock_detail_str = self.get_product_qty_in_stock_detail(product_id.id)

                incoming_moves = product_incoming_moves.get(product_id.id, None)
                if incoming_moves is None:
                    incoming_moves = StockMove.search([("product_id", "=", product_id.id),
                                                       ("location_id", "=", location_suppliers.id),
                                                       "!", ("state", "in", ("done", "cancel"))], order="date_expected")
                    product_incoming_moves[product_id.id] = incoming_moves

                early_moves = filter(lambda m: m.date_expected <= str_product_planned_take_date, incoming_moves)
                late_moves = filter(lambda m: m.date_expected > str_product_planned_take_date, incoming_moves)
                late_moves = late_moves[:1]

                name_and_qties = map(lambda r: "%d(%s,%s)" % (r.product_uom_qty,
                                                              fields.Date.to_string(
                                                                      fields.Datetime.from_string(r.date_expected)),
                                                              r.purchase_line_id.order_id.partner_id.name),
                                     early_moves + late_moves)
                product_incoming_qty = string.join(name_and_qties, "<br/>")

                line["product_code"] = product_id.default_code
                line["product_name"] = product_id.name
                line["product_description"] = product_id.description
                line["product_uom"] = moves[0].product_uom.name
                line["product_qty_available"] = qty_available
                line["qty_in_stock_detail_str"] = qty_in_stock_detail_str
                line["product_incoming_qty"] = product_incoming_qty
                line["product_qty_put"] = reserved_qty
                line["product_need_qty"] = need_qty
                line["product_usage"] = product_usage[product_id.id]
                line["product_remain_qty"] = remain_qty
                line["product_planned_take_date"] = str_product_planned_take_date
                line["order_name"] = order.name
                line["order_product_code"] = order.product_id.default_code
                line["order_product_name"] = order.product_id.name
                line["order_product_name_with_code"] = "%s(%s)" % (order.product_id.name, order.product_id.default_code)
                line["order_origin"] = order.origin if order.origin and order.origin.startswith("SO") else None
                line["order_route_code"] = order.routing_id.code if order.routing_id else None
                line["order_route_name"] = order.routing_id.name if order.routing_id else None
                line["product_source_location"] = order.location_src_id.name
                lines.append(line)
        return lines

    def get_product_qty_in_stock_detail(self, product_id):
        product = self.env["product.product"].browse(product_id)
        qty_in_stock_detail = product.get_qty_in_stock_detail()
        qty_in_stock_detail_str = string.join(
                ("%d(%s)" % (qty_in_stock_detail[key], key) for key in qty_in_stock_detail if
                 qty_in_stock_detail[key] > 0), "<br/>")
        return qty_in_stock_detail_str
