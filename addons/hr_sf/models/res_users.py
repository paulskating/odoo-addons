# _*_ coding: utf-8 _*_
from openerp import models, fields, api


class User(models.Model):
    _inherit = "res.users"

    employee_ids = fields.One2many("hr.employee", "user_id")

    @api.multi
    def get_employee_ids(self):
        self.ensure_one()
        return self.employee_ids.ids
