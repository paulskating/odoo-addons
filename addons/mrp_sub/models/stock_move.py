# _*_ coding: utf-8 _*_
from openerp import models, fields, api, _
from openerp.exceptions import Warning


class StockMove(models.Model):
    _inherit = "stock.move"

    sub_order_id = fields.Many2one("mrp.subcontract", readonly=True)
    sub_order_line_id = fields.Many2one("mrp.subcontract.order.line", readonly=True)
    from_bom_product_id = fields.Many2one("product.product", string="BOM Product", readonly=True)

    sub_origin = fields.Char(compute="_compute_sub_origin")

    @api.multi
    def _compute_sub_origin(self):
        for move in self:
            move.sub_origin = "%s : %s" % (move.sub_order_id and move.sub_order_id.name or "",
                                           move.sub_order_line_id and move.sub_order_line_id.product_id.name or "")

    @api.multi
    def action_wizard_change_product(self):
        self.ensure_one()
        vals = dict()
        vals["from_bom_product_id"] = self.from_bom_product_id.id
        vals["current_product_id"] = self.product_id.id

        wizard = self.env["mrp_sub.change_material_product_wizard"].create(vals)

        return {'type': 'ir.actions.act_window',
                'res_model': wizard._name,
                'res_id': wizard.id,
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new'}

    @api.multi
    def action_change_product(self, to_product_id):
        for move in self:
            if move.state in ("draft", "confirmed"):
                move.product_id = to_product_id
            elif move.state == "assigned":
                move.do_unreserve()
                move.product_id = to_product_id
                move.action_assign()
            else:
                raise Warning(_("Only allow to change product when the stock move is draft or confirmed"))
        return True
