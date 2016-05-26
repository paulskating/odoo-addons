# _*_ coding: utf-8 _*_
from openerp import models, fields, api


class MyhomeOrderLine(models.Model):
    _name = "myhome.order_line"
    order_id = fields.Many2one("myhome.order")
    bank_id = fields.Many2one("myhome.bank",string="Bank_Name",required=True)
    begin = fields.Float()
    end = fields.Float()
    account = fields.Float(compute="_compute_account")

    @api.multi
    def _compute_account(self):
        for line in self:
            line.account = line.end - line.begin





