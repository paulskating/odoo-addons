# _*_ coding: utf-8 _*_
from itertools import groupby
from openerp import models, fields, api, _
from openerp.exceptions import Warning

States_for_only_draft_editable = {"draft": [('readonly', False)],
                                  "confirmed": [('readonly', True)],
                                  "done": [('readonly', True)]}


class Subcontract(models.Model):
    _inherit = ["mail.thread"]
    _name = "mrp.subcontract"

    name = fields.Char('Reference', default='/',
                       required=True, copy=False, readonly=True)

    partner_id = fields.Many2one("res.partner", required=True, states=States_for_only_draft_editable)

    location_src_id = fields.Many2one("stock.location", string="Raw Materials Location", required=True, states=States_for_only_draft_editable)
    location_partner_production_id = fields.Many2one("stock.location", string="Partner Production Location",
                                                     required=True, states=States_for_only_draft_editable)
    location_dest_id = fields.Many2one("stock.location", string="Finished Products Location", required=True, states=States_for_only_draft_editable)
    minimum_planned_data = fields.Date()
    order_date = fields.Datetime(required=True)
    invoice_method = fields.Selection([('manual', 'Based on Purchase Order lines'),
                                       ('order', 'Based on generated draft invoice'),
                                       ('picking', 'Based on incoming shipments')],
                                      'Invoicing Control', required=True, readonly=True,
                                      states=States_for_only_draft_editable)
    line_ids = fields.One2many("mrp.subcontract.order.line", "order_id", "Lines", states=States_for_only_draft_editable)
    scheduled_products_ids = fields.One2many("stock.move", "sub_order_id", "Scheduled Products", readonly=True)

    state = fields.Selection([("draft", "Draft"), ("confirmed", "Confirmed"), ("done", "Done")], default="draft",
                             required=True)

    origin = fields.Char()

    out_picking_count = fields.Integer(compute="_compute_out_picking_count")
    in_picking_count = fields.Integer(compute="_compute_in_picking_count")

    invoice_count = fields.Integer(compute="_compute_invoice_count")

    @api.multi
    def _compute_invoice_count(self):
        Invoice = self.env["account.invoice"]
        for order in self:
            count = Invoice.search_count([("origin", "=", order.name)])
            order.invoice_count = count

    @api.multi
    def _compute_out_picking_count(self):
        Picking = self.env["stock.picking"]
        for order in self:
            count = Picking.search_count([("origin", "=", order.name),
                                          ('picking_type_id', '=',
                                           self.env.ref('mrp_sub.stock_picking_subcontract_out').id)])
            order.out_picking_count = count

    @api.multi
    def _compute_in_picking_count(self):
        Picking = self.env["stock.picking"]
        for order in self:
            count = Picking.search_count([("origin", "=", order.name),
                                          ('picking_type_id', '=',
                                           self.env.ref('mrp_sub.stock_picking_subcontract_in').id)])
            order.in_picking_count = count

    @api.model
    def create(self, vals):
        if vals.get("name", '/') == '/':
            vals['name'] = self.env['ir.sequence'].get('subcontract.order') or '/'
        return super(Subcontract, self).create(vals)

    @api.multi
    def action_wizard_create_out_picking(self):
        self.ensure_one()
        vals = dict()

        # line_vals = list()
        # for line in self.line_ids:
        #     line_vals.append({"product_id": line.product_id.id,
        #                       "product_uom_id": line.product_uom_id.id})
        # vals["line_ids"] = [(0, 0, line_vals)]
        # wizard = self.env["mrp_sub.create_out_picking_wizard"].create(vals)

        wizard = self.env["mrp_sub.create_out_picking_wizard"].create(vals)
        for line in self.line_ids:
            self.env["mrp_sub.create_out_picking_wizard_line"].create({"product_id": line.product_id.id,
                                                                       "product_uom_id": line.product_uom_id.id,
                                                                       "wizard_id": wizard.id})

        return {'type': 'ir.actions.act_window',
                'res_model': wizard._name,
                'res_id': wizard.id,
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new'}

    @api.multi
    def action_confirm(self):
        for order in self:
            if not all((order.location_src_id, order.location_partner_production_id)):
                raise Warning(_(
                        "Please set Raw Materials Location and Partner Production Location on this order %s") % order.name)
            self._explode_bom()
            self._create_out_picking()
            self._create_in_picking()
            order.state = "confirmed"

    @api.multi
    def _create_in_picking(self):
        StockPicking = self.env["stock.picking"]
        StockMove = self.env["stock.move"]
        in_picking_type = self.env.ref("mrp_sub.stock_picking_subcontract_in")
        for order in self:
            if order.line_ids:
                picking = StockPicking.create({"partner_id": order.partner_id.id,
                                               "picking_type_id": in_picking_type.id,
                                               "origin": order.name})
                for line in order.line_ids:
                    vals = dict()
                    vals["name"] = line.product_id.id
                    vals["picking_id"] = picking.id
                    vals["product_id"] = line.product_id.id
                    vals["product_uom_qty"] = line.product_uom_qty
                    vals["product_uom"] = line.product_uom_id.id
                    vals["date_expected"] = line.schedule_date
                    vals["location_id"] = order.location_partner_production_id.id
                    vals["location_dest_id"] = order.location_dest_id.id

                    StockMove.create(vals)

    @api.multi
    def _create_out_picking(self):
        StockPicking = self.env["stock.picking"]
        StockMove = self.env["stock.move"]
        out_picking_type = self.env.ref("mrp_sub.stock_picking_subcontract_out")
        for order in self:
            if order.scheduled_products_ids:
                picking = StockPicking.create({"partner_id": order.partner_id.id,
                                               "picking_type_id": out_picking_type.id,
                                               "origin": order.name})
                picking.move_lines = order.scheduled_products_ids

    def _explode_bom(self):
        for order in self:
            for line in order.line_ids:
                line.explode_bom()

    @api.multi
    def action_cancel(self):
        for order in self:
            order.product_lines.unlink()
        res = super(Subcontract, self).action_cancel()
        return res

    @api.multi
    def action_view_picking_in(self):
        self.ensure_one()
        return self._view_picking("in")

    @api.multi
    def action_view_picking_out(self):
        self.ensure_one()
        return self._view_picking("out")

    @api.multi
    def action_view_invoices(self):
        self.ensure_one()
        Invoice = self.env["account.invoice"]
        action = self.env.ref("account.action_invoice_tree2")
        if not action:
            return True

        action_dict = action.read()[0]

        # TODO not finished
        return True

    @api.multi
    def _view_picking(self, picking_type=None):
        self.ensure_one()
        action = self.env.ref("stock.action_picking_tree")
        if not action:
            return True

        action_dict = action.read()[0]
        domain = [('origin', '=', self.name)]
        if picking_type == "in":
            domain.append(('picking_type_id', '=', self.env.ref('mrp_sub.stock_picking_subcontract_in').id))
        elif picking_type == "out":
            domain.append(('picking_type_id', '=', self.env.ref('mrp_sub.stock_picking_subcontract_out').id))

        action_dict["domain"] = domain
        action_dict["context"] = {}

        return action_dict
