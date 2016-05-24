# _*_ coding: utf-8 _*_
from openerp import models, fields, api


class Product(models.Model):
    _inherit = "product.product"

    qty_in_stock = fields.Float(compute="_compute_qty_in_stock", string="WH数量(可用)")

    @api.multi
    def _compute_qty_in_stock(self):
        for product in self:
            qtys = product.get_qty_in_stock_detail()
            if qtys:
                product.qty_in_stock = sum(qtys.values())

    @api.multi
    def get_qty_in_stock_detail(self):
        self.ensure_one()

        stock_locations = self.env["stock.location"].with_context({'lang': 'en_US'}).search(
                [("name", "in", ("stock", "Stock"))])
        if not stock_locations:
            return None

        qtys = dict()
        for location in stock_locations:
            domain = [("product_id", "=", self.id), ("location_id", "child_of", location.id)]
            quants = self.env["stock.quant"].search(domain)
            qtys[location.complete_name] = sum((q.qty for q in quants))

        return qtys
