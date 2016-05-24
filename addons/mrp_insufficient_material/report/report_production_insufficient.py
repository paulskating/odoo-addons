# _*_ coding: utf-8 _*_
import datetime
import string
from collections import defaultdict
from itertools import groupby

from openerp import models, fields, api


class ReportProductInsufficient(models.AbstractModel):
    _inherit = 'report.mrp_insufficient_material.report_product_insufficient'
    _name = 'report.mrp_insufficient_material.report_production_insufficient'

    @api.multi
    def render_html(self, data=None):
        lines = self.get_report_lines(data)

        groups = groupby(lines, lambda l: (l["product_id"],
                                           l["product_code"],
                                           l["product_name"],
                                           l["product_description"],
                                           l["product_uom"],
                                           l["qty_in_stock_detail_str"],
                                           l["product_incoming_qty"],))
        lines2 = dict()

        for g, v in groups:
            lines2[g] = list(v)

        for key in lines2:
            print key,lines2[key]

        docargs = {
            "date": fields.Date.today(),
            "lines": lines2,
            "filter_by": data.get("filter_by", None),
            "date_to": data.get("date_to", None),
            "order_from": data.get("order_from", None),
            "order_to": data.get("order_to", None),
            "order_names": string.join(self.env["mrp.production"].browse(data.get("order_ids", [])).mapped("name"),
                                       ","),
            "product_names": string.join(self.env["product.product"].browse(data.get("product_ids", [])).mapped("name"),
                                         ",")
        }
        return self.env['report'].render('mrp_insufficient_material.report_production_insufficient_template',
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
        product_remain = dict()
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

                if product_id.id not in product_remain:
                    product_remain[product_id.id] = product_id.qty_in_stock

                if product_remain[product_id.id] <= 0:
                    lack_qty = need_qty
                else:
                    lack_qty = abs(product_remain[product_id.id] - need_qty)
                    product_remain[product_id.id] -= need_qty
                    if product_remain[product_id.id] < 0:
                        product_remain[product_id.id] = 0

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

                name_and_qties = map(lambda r: "%d(%s)" % (r.product_uom_qty,
                                                           fields.Date.to_string(
                                                                   fields.Datetime.from_string(r.date_expected))),
                                     early_moves + late_moves)
                product_incoming_qty = string.join(name_and_qties, "<br/>")

                line["product_id"] = product_id.id
                line["product_code"] = product_id.default_code
                line["product_name"] = product_id.name
                line["product_description"] = product_id.description
                line["product_uom"] = moves[0].product_uom.name
                line["product_qty_in_stock"] = product_id.qty_in_stock
                line["qty_in_stock_detail_str"] = qty_in_stock_detail_str
                line["product_incoming_qty"] = product_incoming_qty
                line["product_qty_put"] = reserved_qty
                line["product_need_qty"] = need_qty
                line["product_usage"] = product_usage[product_id.id]
                line["lack_qty"] = lack_qty
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
