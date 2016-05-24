# _*_ coding: utf-8 _*_
from openerp import models, fields, api

class lessonManage(models.Model):
    _name="lesson"

    le_name = fields.Char()
    le_credit = fields.Float()
    teacher_id = fields.Many2one("teacher",
                              string="Teacher",
                              required=True)


