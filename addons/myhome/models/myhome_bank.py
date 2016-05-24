# _*_ coding: utf-8 _*_
from openerp import models, fields, api


class MyhomeBank(models.Model):
    _name = "myhome.bank"
    _rec_name = "bank_name"

    bank_name = fields.Char()
    bank_category = fields.Char()


    line = fields.One2many("myhome.order_line","bank_id")

