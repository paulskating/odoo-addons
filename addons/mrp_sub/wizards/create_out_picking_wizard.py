# _*_ coding: utf-8 _*_
from openerp import models, fields, api


class CreateOutPickingWizardLine(models.TransientModel):
    _name = "mrp_sub.create_out_picking_wizard_line"

    wizard_id = fields.Many2one("mrp_sub.create_out_picking_wizard")
    product_id = fields.Many2one("product.product", string="Product To Product", readonly=True)
    product_uom_id = fields.Many2one("product.uom", string="Product UOM", readonly=True)
    product_uom_qty = fields.Float(string="Quantity")


class CreateOutPickingWizard(models.TransientModel):
    _name = "mrp_sub.create_out_picking_wizard"

    line_ids = fields.One2many("mrp_sub.create_out_picking_wizard_line", "wizard_id")
    count = fields.Integer()

    @api.multi
    def create_out_picking(self):
        pass
