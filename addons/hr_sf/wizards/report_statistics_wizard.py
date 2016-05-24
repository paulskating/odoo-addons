# _*_ coding: utf-8 _*_
from openerp import models, fields, api


class ReportStatisticsWizard(models.Model):
    _inherit = "hr_sf.report_wizard_base"
    _name = "hr_sf.report_statistics_wizard"

    repeat_header = fields.Boolean()

    @api.multi
    def action_OK(self):
        self.ensure_one()
        data = self.get_input_values()
        data["repeat_header"] = self.repeat_header
        return self.env['report'].get_action(self, 'hr_sf.report_attendance_statistics', data=data)
