# _*_ coding: utf-8 _*_
import datetime
from openerp import models, fields, api
from openerp.fields import Date
from openerp.tools.misc import DEFAULT_SERVER_TIME_FORMAT

from ..tools.TimeZoneHelper import UTC_Datetime_To_TW_TZ
from ..tools.TimeZoneHelper import UTC_String_From_TW_TZ


class Attendance(models.Model):
    _inherit = "hr.attendance"

    location = fields.Char(required=True)
    code = fields.Char(related="employee_id.internal_code", readonly=True)

    upload_log_id = fields.Many2one("hr_sf.attendance_upload_Log", string="Upload log")

    morning_start_work_time = fields.Char(readonly=True)
    morning_end_work_time = fields.Char(readonly=True)
    afternoon_start_work_time = fields.Char(readonly=True)
    afternoon_end_work_time = fields.Char(readonly=True)

    # late_minutes = fields.Float(compute="_compute_late_minutes", store=True)
    # early_minutes = fields.Float(compute="_compute_early_minutes", store=True)
    overtime_hours = fields.Float(compute="_compute_overtime_hours", store=True)

    forget_card = fields.Boolean(default=True)

    # @api.depends("name", "action")
    # @api.multi
    # def _compute_late_minutes(self):
    #     for attendance in self:
    #         if attendance.action == "sign_in" and attendance.morning_start_work_time:
    #             dt_action_time = UTC_Datetime_To_TW_TZ(attendance.name).time()
    #             dt_start_work_time = datetime.datetime.strptime(attendance.morning_start_work_time,
    #                                                             DEFAULT_SERVER_TIME_FORMAT).time()
    #             if dt_action_time > dt_start_work_time:
    #                 now = datetime.datetime.now()
    #                 dt_action_time = datetime.datetime(year=now.year, month=now.month, day=now.day,
    #                                                    hour=dt_action_time.hour,
    #                                                    minute=dt_action_time.minute,
    #                                                    second=dt_action_time.second)
    #                 dt_start_work_time = datetime.datetime(year=now.year, month=now.month, day=now.day,
    #                                                        hour=dt_start_work_time.hour,
    #                                                        minute=dt_start_work_time.minute,
    #                                                        second=dt_start_work_time.second)
    #                 attendance.late_minutes = (dt_action_time - dt_start_work_time).seconds / 60.0
    #
    # @api.depends("name", "action")
    # @api.multi
    # def _compute_early_minutes(self):
    #     for attendance in self:
    #         if attendance.action == "sign_out" and attendance.afternoon_end_work_time:
    #             dt_action_time = UTC_Datetime_To_TW_TZ(attendance.name).time()
    #             dt_end_work_time = datetime.datetime.strptime(attendance.afternoon_end_work_time,
    #                                                           DEFAULT_SERVER_TIME_FORMAT).time()
    #             if dt_action_time < dt_end_work_time:
    #                 now = datetime.datetime.now()
    #                 dt_action_time = datetime.datetime(year=now.year, month=now.month, day=now.day,
    #                                                    hour=dt_action_time.hour,
    #                                                    minute=dt_action_time.minute,
    #                                                    second=dt_action_time.second)
    #                 dt_end_work_time = datetime.datetime(year=now.year, month=now.month, day=now.day,
    #                                                      hour=dt_end_work_time.hour,
    #                                                      minute=dt_end_work_time.minute,
    #                                                      second=dt_end_work_time.second)
    #                 attendance.early_minutes = (dt_end_work_time - dt_action_time).seconds / 60.0

    @api.multi
    def _altern_si_so(self):
        return True

    _constraints = [
        (_altern_si_so, 'Error ! Sign in (resp. Sign out) must follow Sign out (resp. Sign in)', ['action'])]

    @api.multi
    def adjust(self, date_from=None, date_to=None):
        if not any((date_from, date_to)):
            dt_date_from = fields.Date.from_string(fields.Date.today())
            dt_date_to = fields.Date.from_string(fields.Date.today())
        elif all((date_from, date_to)):
            dt_date_from = fields.Date.from_string(date_from)
            dt_date_to = fields.Date.from_string(date_to)
        else:
            return True

        dt_date = dt_date_from
        while dt_date <= dt_date_to:
            domain = [("name", ">=",
                       fields.Datetime.to_string(
                               datetime.datetime(dt_date.year, dt_date.month, dt_date.day) + datetime.timedelta(
                                       hours=- 8, minutes=0, seconds=0))),
                      ("name", "<=",
                       fields.Datetime.to_string(
                               datetime.datetime(dt_date.year, dt_date.month, dt_date.day) + datetime.timedelta(
                                       hours=23 - 8, minutes=59, seconds=59)))]
            records = self.search(domain)
            if records:
                employees = records.mapped("employee_id")
                for emp in employees:
                    emp_records = records.filtered(lambda r: r.employee_id == emp)
                    emp_records.write({"action": "action"})

                    emp_records = [r for r in emp_records.sorted(key=lambda r: r.name)]
                    if emp_records:
                        emp_records_filtered = list()
                        for rec in emp_records:
                            if not emp_records_filtered:
                                emp_records_filtered.append(rec)
                            else:
                                dt_date_latest_added = fields.Datetime.from_string(emp_records_filtered[-1].name)
                                cur_date = fields.Datetime.from_string(rec.name)
                                if (cur_date - dt_date_latest_added) > datetime.timedelta(minutes=5):
                                    emp_records_filtered.append(rec)
                        emp_records_filtered_recordset = reduce(lambda x, y: x + y, emp_records_filtered)
                        if len(emp_records_filtered_recordset) == 1:
                            dt_action_time = fields.Datetime.from_string(emp_records_filtered_recordset.name)
                            if (dt_action_time + datetime.timedelta(hours=8)).hour < 12:
                                emp_records_filtered_recordset[0].action = "sign_in"
                            else:
                                emp_records_filtered_recordset[0].action = "sign_out"
                        if len(emp_records_filtered) > 1:
                            emp_records_filtered_recordset[0].action = "sign_in"
                            emp_records_filtered_recordset[-1].action = "sign_out"
            dt_date += datetime.timedelta(days=1)
        return True

    @api.model
    def create(self, vals):
        ConfigParameter = self.env['ir.config_parameter'].sudo()
        morning_start_work_time = ConfigParameter.get_param('morning_start_work_time')
        morning_end_work_time = ConfigParameter.get_param('morning_end_work_time')
        afternoon_start_work_time = ConfigParameter.get_param('afternoon_start_work_time')
        afternoon_end_work_time = ConfigParameter.get_param('afternoon_end_work_time')
        vals["morning_start_work_time"] = morning_start_work_time
        vals["morning_end_work_time"] = morning_end_work_time
        vals["afternoon_start_work_time"] = afternoon_start_work_time
        vals["afternoon_end_work_time"] = afternoon_end_work_time
        return super(Attendance, self).create(vals)

    @api.depends("name", "action")
    @api.multi
    def _compute_overtime_hours(self):
        for attendance in self:
            attendance.overtime_hours = 9.99
