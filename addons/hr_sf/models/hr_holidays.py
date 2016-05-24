# _*_ coding: utf-8 _*_
import datetime
from openerp import models, fields, api, _
from openerp.fields import Datetime
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.exceptions import Warning


class Holiday(models.Model):
    _inherit = "hr.holidays"

    leave_duration = fields.Float(compute="_compute_leave_duration", store=True)

    morning_start_work_time = fields.Char(readonly=True, default=lambda self: self.env[
        'ir.config_parameter'].sudo().get_param('morning_start_work_time'))
    morning_end_work_time = fields.Char(readonly=True, default=lambda self: self.env[
        'ir.config_parameter'].sudo().get_param('morning_end_work_time'))
    afternoon_start_work_time = fields.Char(readonly=True, default=lambda self: self.env[
        'ir.config_parameter'].sudo().get_param('afternoon_start_work_time'))
    afternoon_end_work_time = fields.Char(readonly=True, default=lambda self: self.env[
        'ir.config_parameter'].sudo().get_param('afternoon_end_work_time'))

    @api.depends("date_from", "date_to")
    @api.multi
    def _compute_leave_duration(self):
        for holiday in self:
            if all((holiday.morning_start_work_time, holiday.morning_end_work_time,
                    holiday.afternoon_start_work_time, holiday.afternoon_end_work_time)):
                if not all((holiday.date_from, holiday.date_to)):
                    continue
                dt_holiday_from = Datetime.from_string(holiday.date_from) + datetime.timedelta(hours=8)
                dt_holiday_to = Datetime.from_string(holiday.date_to) + datetime.timedelta(hours=8)

                leave = datetime.timedelta()

                dt_date = dt_holiday_from.date()
                while dt_date <= dt_holiday_to.date():
                    querying_day = dt_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
                    dt_the_day_morning_start_work_time = datetime.datetime.strptime(
                            "%s %s" % (querying_day, holiday.morning_start_work_time), DEFAULT_SERVER_DATETIME_FORMAT)
                    dt_the_day_morning_end_work_time = datetime.datetime.strptime(
                            "%s %s" % (querying_day, holiday.morning_end_work_time), DEFAULT_SERVER_DATETIME_FORMAT)
                    dt_the_day_afternoon_start_work_time = datetime.datetime.strptime(
                            "%s %s" % (querying_day, holiday.afternoon_start_work_time), DEFAULT_SERVER_DATETIME_FORMAT)
                    dt_the_day_afternoon_end_work_time = datetime.datetime.strptime(
                            "%s %s" % (querying_day, holiday.afternoon_end_work_time), DEFAULT_SERVER_DATETIME_FORMAT)

                    # deal with morning first
                    dt_cal_start = max(dt_the_day_morning_start_work_time, dt_holiday_from)
                    dt_cal_start = min(dt_cal_start, dt_the_day_morning_end_work_time)

                    dt_cal_end = min(dt_the_day_morning_end_work_time, dt_holiday_to)
                    dt_cal_end = max(dt_cal_end, dt_the_day_morning_start_work_time)

                    if dt_cal_end > dt_cal_start:
                        leave += dt_cal_end - dt_cal_start

                    # then deal with afternoon first
                    dt_cal_start = max(dt_the_day_afternoon_start_work_time, dt_holiday_from)
                    dt_cal_start = min(dt_cal_start, dt_the_day_afternoon_end_work_time)

                    dt_cal_end = min(dt_the_day_afternoon_end_work_time, dt_holiday_to)
                    dt_cal_end = max(dt_cal_end, dt_the_day_afternoon_start_work_time)

                    if dt_cal_end > dt_cal_start:
                        leave += dt_cal_end - dt_cal_start

                    dt_date += datetime.timedelta(days=1)

                holiday.leave_duration = leave.days * 24.0 + leave.seconds / 3600.0

    @api.multi
    def holidays_confirm(self):
        super(Holiday, self).holidays_confirm()

        for holiday in self:
            coach = holiday.employee_id.coach_id
            manager = holiday.employee_id.parent_id
            if coach and coach.user_id:
                holiday.message_subscribe_users(user_ids=coach.user_id.ids)
            if holiday.leave_duration >= 16 and manager and manager.user_id:
                holiday.message_subscribe_users(user_ids=manager.user_id.ids)
            elif holiday.leave_duration < 16 and manager and manager.user_id:
                holiday.message_unsubscribe_users(user_ids=manager.user_id.ids)
