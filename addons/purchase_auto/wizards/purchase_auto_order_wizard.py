# _*_ coding: utf-8 _*_
from openerp import models, fields, api


class PurchaseAutoOrderWizard(models.TransientModel):
    _name = "purchase_auto_order_wizard"

    company_id = fields.Many2one("res.company")
    warehouse_id = fields.Many2one("stock.warehouse")
    location_id = fields.Many2one("stock.location")

    @api.multi
    def action_ok(self):
        self.ensure_one()
        AutoOrder = self.env["purchase.auto_order"]
        vals = dict()
        vals["company_id"] = self.company_id.id
        vals["warehouse_id"] = self.warehouse_id.id
        vals["location_id"] = self.location_id.id

        line_vals = list()
        order = AutoOrder.create(vals)

        AutoOrderLine = self.env["purchase.auto_order.line"]

        OrderPoint = self.env["stock.warehouse.orderpoint"]
        ops = OrderPoint.search([("location_id","=",self.location_id.id)])
        products_ids =set(ops.mapped("product_id").ids)

        #all_products = self.env["product.template"].search([])
        # for p in all_products:
        #     AutoOrderLine.create({
        #         "product_id": p.id,
        #         "order_id":order.id
        #     })

        for p_id in products_ids:
            AutoOrderLine.create({
                    "product_id": p_id,
                    "order_id":order.id
                })


        return {'type': 'ir.actions.act_window',
                'res_model': order._name,
                'res_id': order.id,
                'view_type': 'form',
                'view_mode': 'form',
                }

