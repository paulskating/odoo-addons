# _*_ coding: utf-8 _*_
from openerp import models, fields, api


class teacherManage(models.Model):
    _name="teacher"
    _rec_name = "te_name"
    te_name = fields.Char()
    te_age = fields.Integer()
    te_email = fields.Char()
    te_tel = fields.Char()
    te_lesson = fields.One2many("lesson","teacher_id")
    te_student_ids = fields.One2many("stu.student", "s_teacher_id")