# _*_ coding: utf-8 _*_
from openerp import models, fields, api


class ReportProductInsufficientWizard(models.TransientModel):
    _inherit = "mrp_insufficient_material.report_product_insuf_wizard"
    _name = "mrp_insufficient_material.report_production_insuf_wizard"

    # filter_by = fields.Selection([("date", "Date"), ("order_number", "Order Number")], required=True)
    # date_to = fields.Date()
    # order_number_from = fields.Char()
    # order_number_to = fields.Char()
    # location_ids = fields.Many2many("stock.location", string="Stock Locations",
    #                                 relation="mrp_insufficient_material_rpt_prodtn_insuf_loc_rel")
    #
    # product_ids = fields.Many2many("product.product", string="Products",
    #                                relation="mrp_insufficient_material_rpt_prodtn_insuf_product_rel")
    # routing_ids = fields.Many2many("mrp.routing", string="Routings",
    #                                relation="mrp_insufficient_material_rpt_prodtn_insuf_routing_rel")

    #
    # only_print_insufficient = fields.Boolean()
    # allow_print_zero_use = fields.Boolean()
    #

    order_ids = fields.Many2many("mrp.production", relation="mrp_insufficient_material_rpt_production_insuf_mo_rel")

    product_ids = fields.Many2many("product.product",
                                   relation="mrp_insufficient_material_rpt_production_insuf_product_rel")

    location_ids = fields.Many2many("stock.location", string="Stock Locations",
                                    relation="mrp_insufficient_material_rpt_production_insuf_loc_rel")

    @api.multi
    def action_print(self):
        self.ensure_one()
        data = self.get_data()
        return self.env["report"].get_action(self, "mrp_insufficient_material.report_production_insufficient",
                                             data=data)
