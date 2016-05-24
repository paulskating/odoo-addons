# _*_ coding: utf-8 _*_
import datetime
from openerp import models, fields, api


class ReportWizard(models.Model):
    _name = "hr_sf.report_wizard_base"

    @api.multi
    def _get_default_date_from(self):
        dt_now = fields.Date.from_string(fields.Datetime.now())
        return fields.Date.to_string(datetime.date(dt_now.year, dt_now.month, 1))

    date_from = fields.Date(default=_get_default_date_from)
    date_to = fields.Date(default=lambda self: fields.date.today())

    filter_by = fields.Selection([("none", "No filter"),
                                  ("department", "Department"),
                                  ("employee", "Employee")], default="none")
    employee_ids = fields.Many2many("hr.employee")
    department_ids = fields.Many2many("hr.department")

    export_as_xls = fields.Boolean()
    xls_file = fields.Binary()
    xls_file_name = fields.Char()

    export_as_xls_generated = fields.Boolean()

    state = fields.Selection([('step1', 'step1'), ('step2', 'step2')], default="step1")

    @api.multi
    def get_input_values(self):
        self.ensure_one()
        data = dict()
        if all((self.date_from, self.date_to)):
            data["date_from"] = self.date_from
            data["date_to"] = self.date_to
        data["filter_by"] = self.filter_by
        data["employee_ids"] = self.employee_ids.mapped("id")
        data["department_ids"] = self.department_ids.mapped("id")
        return data

    @api.multi
    def next_step(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window',
                'res_model': self._name,
                'res_id': self.id,
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new'}
