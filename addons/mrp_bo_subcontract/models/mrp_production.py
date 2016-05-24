# _*_ coding: utf-8 _*_
from openerp import models, fields, api


class Production(models.Model):
    _inherit = "mrp.production"

    in_picking_count = fields.Integer(compute="_compute_in_picking_count")

    @api.multi
    def _compute_in_picking_count(self):
        self.ensure_one()

        domain = [('origin', '=', self.name)]

        if self.routing_id and self.routing_id.picking_type_id:
            domain.append(('picking_type_id', '=', self.routing_id.picking_type_id.id))

        count = self.env["stock.picking"].search_count(domain)
        self.in_picking_count = count

    @api.model
    def action_produce(self, production_id, production_qty, production_mode, wiz=False):
        res = super(Production, self).action_produce(production_id, production_qty, production_mode, wiz)
        if production_mode == "consume_produce":
            production = self.browse(production_id)
            if production.routing_id and \
                    production.routing_id.is_create_picking and \
                    production.routing_id.picking_type_id:
                default_location_src_id = production.location_dest_id
                default_location_dest_id = production.routing_id.picking_type_id.default_location_dest_id
                if default_location_src_id != default_location_dest_id:
                    Picking = self.env["stock.picking"]
                    picking_vals = {
                        "partner_id": production.supplier.id,
                        "picking_type_id": production.routing_id.picking_type_id.id,
                        "origin": production.name
                    }

                    move_vals = {
                        "name": production.product_id.name,
                        #"picking_id": picking.id,
                        "product_id": production.product_id.id,
                        "product_uom_qty": production_qty,
                        "product_uom": production.product_uom.id,
                        "date_expected": production.date_planned,
                        "location_id": default_location_src_id.id,
                        "location_dest_id": default_location_dest_id.id
                    }
                    picking_vals["move_lines"] = [(0, 0, move_vals)]
                    picking = Picking.create(picking_vals)
                    # self.env["stock.move"].create(move_vals)

        return res


    @api.multi
    def action_view_in_picking(self, picking_type=None):
        self.ensure_one()
        action = self.env.ref("stock.action_picking_tree")
        if not action:
            return True

        action_dict = action.read()[0]
        domain = [('origin', '=', self.name)]

        if self.routing_id and self.routing_id.picking_type_id:
            domain.append(('picking_type_id', '=', self.routing_id.picking_type_id.id))

        action_dict["domain"] = domain
        action_dict["context"] = {}

        return action_dict