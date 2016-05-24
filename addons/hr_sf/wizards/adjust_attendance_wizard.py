# _*_ coding: utf-8 _*_
from openerp import models, fields, api


class AdjustAttendanceWizard(models.TransientModel):
    _name = "hr_sf.adjust_attendance_wizard"

    date_from = fields.Date(default=lambda self: fields.date.today())
    date_to = fields.Date(default=lambda self: fields.date.today())

    @api.multi
    def action_OK(self):
        self.ensure_one()
        Attendance = self.env["hr.attendance"]
        if not all((self.date_from, self.date_to)):
            Attendance.adjust()
        else:
            Attendance.adjust(self.date_from, self.date_to)
