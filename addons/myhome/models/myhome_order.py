# _*_ coding: utf-8 _*_
from openerp import models, fields, api


class MyhomeOrder(models.Model):
    _name = "myhome.order"

    order_date = fields.Date()
    state = fields.Char()
    order_line = fields.One2many("myhome.order_line", "order_id")
    notes = fields.Text()
    untaxed = fields.Float(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all', track_visibility='always')
    tax = fields.Float(string='Taxes', store=True, readonly=True, compute='amount_all')
    total = fields.Float(string='Total', store=True, readonly=True, compute='amount_all')


    @api.multi
    def action_confirm(self):
        pass

    @api.multi
    def amount_all(self):
        pass

