# _*_ coding: utf-8 _*_
from openerp import models, fields, api


class PurchaseAutoOrderLine(models.Model):
    _name = "purchase.auto_order.line"

    product_id = fields.Many2one("product.product", readonly=True)
    qty_on_hand = fields.Float(related="product_id.qty_available", readonly=True)
    min_stock = fields.Integer(compute="_compute_min_stock")
    qty_suggest = fields.Float(compute="_compute_qty_suggest")
    qty = fields.Float()

    supplier_id = fields.Many2one("res.partner", compute="_compute_supplier_id")

    order_id = fields.Many2one("purchase.auto_order")

    @api.multi
    def _compute_min_stock(self):
        pass

    @api.multi
    @api.depends("qty_on_hand","min_stock")
    def _compute_qty_suggest(self):
        for line in self:
            line.qty_suggest = line.min_stock - line.qty_on_hand

    @api.multi
    def _compute_supplier_id(self):
        pass