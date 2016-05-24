# _*_ coding: utf-8 _*_
from openerp import models, fields, api
from openerp.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def action_confirm(self):
        raise UserError("not allowed")