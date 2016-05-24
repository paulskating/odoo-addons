# _*_ coding: utf-8 _*_
from openerp import models, fields, api


class MyhomeBank(models.Model):
    _name = "myhome.bank"

    bank_name = fields.Char()
    bank_category = fields.Char()

