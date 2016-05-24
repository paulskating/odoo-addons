# _*_ coding: utf-8 _*_
from openerp import models, fields, api


class PurchaseAutoOrder(models.Model):
    _inherit = "mail.thread"
    _name = "purchase.auto_order"

    name = fields.Char()

    company_id = fields.Many2one("res.company")
    warehouse_id = fields.Many2one("stock.warehouse")
    location_id = fields.Many2one("stock.location")

    order_lines = fields.One2many("purchase.auto_order.line","order_id",
                                  string="Order Lines")

    state = fields.Selection([("draft","Draft"),
                              ("confirmed","Confirmed")])

    @api.multi
    def action_confirm(self):
        PurchaseOrder = self.env["purchase.order"]
        PurchaseOrderLine = self.env["purchase.order.line"]
        order = PurchaseOrder.create({
            "partner_id":8
        })
        for line in self.order_lines:
            PurchaseOrderLine.create({
                "name":line.product_id.name,
                "order_id":order.id,
                "product_id":line.product_id.id,
                "date_planned":fields.datetime.today(),
                "product_qty":line.qty,
                "product_uom":1,
                "price_unit":5
            })
