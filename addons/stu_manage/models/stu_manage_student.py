# _*_ coding: utf-8 _*_
from openerp import models, fields, api


class stuManage(models.Model):
    _name = "stu.student"

    stu_no = fields.Char()
    stu_name = fields.Char()
    stu_age = fields.Integer()
    stu_email = fields.Char()
    stu_birthday = fields.Date()
    s_teacher_id = fields.Many2one("teacher",
                                   string="Teacher",
                                   required=True)
