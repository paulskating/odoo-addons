# _*_ coding: utf-8 _*_
from openerp import models, fields, api


class MyhomeItme(models.Model):
    _name = "myhome.item"
    _rec_name = "item_name"


    item_name = fields.Char()
    item_out = fields.Float()
    item_in = fields.Float()
    item_description = fields.Char()
    item_id=fields.Many2one("myhome.company")