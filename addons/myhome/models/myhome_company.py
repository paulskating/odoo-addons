# _*_ coding: utf-8 _*_
from openerp import models, fields, api


class MyhomeCompany(models.Model):
    _name = "myhome.company"


    company_date = fields.Date()
    company_id = fields.One2many("myhome.item","item_id")
