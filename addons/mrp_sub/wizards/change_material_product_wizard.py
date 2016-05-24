# _*_ coding: utf-8 _*_
from openerp import models, fields, api


class ChangeMaterialProductWizard(models.TransientModel):
    _name = "mrp_sub.change_material_product_wizard"

    from_bom_product_id = fields.Many2one("product.product", string="BOM Product", readonly=True)
    current_product_id = fields.Many2one("product.product", string="Current Product", readonly=True)
    new_product_id = fields.Many2one("product.product", string="Change To Product", required=True)

    @api.multi
    def action_change_product(self):
        self.ensure_one()
        active_id = self.env.context.get("active_id", None)
        if not active_id:
            return True

        move = self.env["stock.move"].browse(active_id)

        return move.action_change_product(to_product_id=self.new_product_id.id)
