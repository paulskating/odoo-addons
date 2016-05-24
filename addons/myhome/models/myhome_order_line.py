# _*_ coding: utf-8 _*_
from openerp import models, fields, api


class MyhomeOrderLine(models.Model):
    _name = "myhome.order_line"
    order_id = fields.Many2one("myhome.order")

