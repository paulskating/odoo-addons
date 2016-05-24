# _*_ coding: utf-8 _*_
from openerp import models, fields, api


class MyhomeOrder(models.Model):
    _name = "myhome.order"

    order_date = fields.Date()
    state = fields.Char()
    order_line = fields.One2many("myhome.order_line", "order_id")

    @api.multi
    def action_confirm(self):
        pass

