# _*_ coding: utf-8 _*_
import datetime
import string
from collections import defaultdict
from openerp import models, fields, api, _
from openerp.fields import Date
from openerp.fields import Datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools import DEFAULT_SERVER_TIME_FORMAT
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

from ..tools.TimeZoneHelper import UTC_String_From_TW_TZ
from ..tools.TimeZoneHelper import UTC_String_To_TW_TZ
from ..tools.TimeZoneHelper import UTC_Datetime_From_TW_TZ
from ..tools.TimeZoneHelper import UTC_Datetime_To_TW_TZ


class Employee(models.Model):
    _inherit = "hr.employee"

    card_code = fields.Char(help="考勤卡卡号。")
    internal_code = fields.Char()
    responsibility = fields.Boolean(help="用于标识这个员工是不是责任制。")

    holidays_ids = fields.One2many("hr.holidays", "employee_id")

    # @api.multi
    # def get_attendance(self, date=None, location=None):
    #     self.ensure_one()
    #     HRAttendance = self.env["hr.attendance"].sudo()
    #     domain = []
    #     if date:
    #         domain.append(("name", "=like", "%s%%" % date))
    #     if location:
    #         domain.append(("location", "=", location))
    #
    #     records = HRAttendance.search(domain)
    #     return records

    @api.multi
    def get_absent_on(self, date=None):
        self.ensure_one()
        if not date:
            return None

        querying_day = date
        if isinstance(date, datetime.date):
            querying_day = Date.to_string(date)

        absent_type = self.env.ref("hr_sf.absent_holidays_status")
        absent_type_id = absent_type.id

        for holiday in self.holidays_ids:
            if not holiday.date_from or not holiday.date_to:
                continue
            if holiday.holiday_status_id.id != absent_type_id:
                continue

            if not all((holiday.morning_start_work_time,
                        holiday.morning_end_work_time,
                        holiday.afternoon_start_work_time,
                        holiday.afternoon_end_work_time)):
                return None

            dt_the_day_morning_start_work_time = datetime.datetime.strptime(
                    "%s %s" % (querying_day, holiday.morning_start_work_time), DEFAULT_SERVER_DATETIME_FORMAT)
            dt_the_day_morning_end_work_time = datetime.datetime.strptime(
                    "%s %s" % (querying_day, holiday.morning_end_work_time), DEFAULT_SERVER_DATETIME_FORMAT)
            dt_the_day_afternoon_start_work_time = datetime.datetime.strptime(
                    "%s %s" % (querying_day, holiday.afternoon_start_work_time), DEFAULT_SERVER_DATETIME_FORMAT)
            dt_the_day_afternoon_end_work_time = datetime.datetime.strptime(
                    "%s %s" % (querying_day, holiday.afternoon_end_work_time), DEFAULT_SERVER_DATETIME_FORMAT)

            dt_holiday_from = Datetime.from_string(holiday.date_from) + datetime.timedelta(hours=8)
            dt_holiday_to = Datetime.from_string(holiday.date_to) + datetime.timedelta(hours=8)

            # deal with morning first
            dt_cal_start = max(dt_the_day_morning_start_work_time, dt_holiday_from)
            dt_cal_start = min(dt_cal_start, dt_the_day_morning_end_work_time)

            dt_cal_end = min(dt_the_day_morning_end_work_time, dt_holiday_to)
            dt_cal_end = max(dt_cal_end, dt_the_day_morning_start_work_time)

            if dt_cal_end > dt_cal_start:
                return absent_type.name

            # then deal with afternoon first
            dt_cal_start = max(dt_the_day_afternoon_start_work_time, dt_holiday_from)
            dt_cal_start = min(dt_cal_start, dt_the_day_afternoon_end_work_time)

            dt_cal_end = min(dt_the_day_afternoon_end_work_time, dt_holiday_to)
            dt_cal_end = max(dt_cal_end, dt_the_day_afternoon_start_work_time)

            if dt_cal_end > dt_cal_start:
                return absent_type.name

    @api.multi
    def get_holiday_on(self, date=None):
        self.ensure_one()
        if not date:
            return None

        querying_day = date
        if isinstance(date, datetime.date):
            querying_day = Date.to_string(date)

        leaves = defaultdict(lambda: list())  # [None, None, datetime.timedelta()] _time = datetime.timedelta()

        absent_type_id = self.env.ref("hr_sf.absent_holidays_status").id

        for holiday in self.holidays_ids:
            if not holiday.date_from or not holiday.date_to:
                continue
            if holiday.holiday_status_id.id == absent_type_id:
                continue
            if holiday.state not in ("validate", "validate1"):
                continue

            if not all((holiday.morning_start_work_time,
                        holiday.morning_end_work_time,
                        holiday.afternoon_start_work_time,
                        holiday.afternoon_end_work_time)):
                return None

            dt_the_day_morning_start_work_time = datetime.datetime.strptime(
                    "%s %s" % (querying_day, holiday.morning_start_work_time), DEFAULT_SERVER_DATETIME_FORMAT)
            dt_the_day_morning_end_work_time = datetime.datetime.strptime(
                    "%s %s" % (querying_day, holiday.morning_end_work_time), DEFAULT_SERVER_DATETIME_FORMAT)
            dt_the_day_afternoon_start_work_time = datetime.datetime.strptime(
                    "%s %s" % (querying_day, holiday.afternoon_start_work_time), DEFAULT_SERVER_DATETIME_FORMAT)
            dt_the_day_afternoon_end_work_time = datetime.datetime.strptime(
                    "%s %s" % (querying_day, holiday.afternoon_end_work_time), DEFAULT_SERVER_DATETIME_FORMAT)

            dt_holiday_from = Datetime.from_string(holiday.date_from) + datetime.timedelta(hours=8)
            dt_holiday_to = Datetime.from_string(holiday.date_to) + datetime.timedelta(hours=8)
            # deal with morning first
            dt_cal_start = max(dt_the_day_morning_start_work_time, dt_holiday_from)
            dt_cal_start = min(dt_cal_start, dt_the_day_morning_end_work_time)

            dt_cal_end = min(dt_the_day_morning_end_work_time, dt_holiday_to)
            dt_cal_end = max(dt_cal_end, dt_the_day_morning_start_work_time)

            if dt_cal_end > dt_cal_start:
                leaves[holiday.holiday_status_id.name].append((dt_cal_start, dt_cal_end, dt_cal_end - dt_cal_start))
                # leaves[holiday.holiday_status_id.name][0] = dt_cal_start
                # leaves[holiday.holiday_status_id.name][1] = dt_cal_end
                # leaves[holiday.holiday_status_id.name][2] += dt_cal_end - dt_cal_start

            # then deal with afternoon first
            dt_cal_start = max(dt_the_day_afternoon_start_work_time, dt_holiday_from)
            dt_cal_start = min(dt_cal_start, dt_the_day_afternoon_end_work_time)

            dt_cal_end = min(dt_the_day_afternoon_end_work_time, dt_holiday_to)
            dt_cal_end = max(dt_cal_end, dt_the_day_afternoon_start_work_time)

            if dt_cal_end > dt_cal_start:
                leaves[holiday.holiday_status_id.name].append((dt_cal_start, dt_cal_end, dt_cal_end - dt_cal_start))
                # leaves[holiday.holiday_status_id.name][0] = dt_cal_start
                # leaves[holiday.holiday_status_id.name][1] = dt_cal_end
                # leaves[holiday.holiday_status_id.name][2] += dt_cal_end - dt_cal_start

        return leaves

    @api.multi
    def get_start_work_time_on(self, date=None):
        self.ensure_one()
        if not date:
            return None

        attendance = self.get_sign_in_attendance(date)

        return UTC_Datetime_To_TW_TZ(attendance.name) if attendance else None

    @api.multi
    def get_work_duration_on(self, date=None):
        self.ensure_one()
        if not date:
            return None

        sign_in_attendance = self.get_sign_in_attendance(date)
        sign_out_attendance = self.get_sign_out_attendance(date)
        if sign_in_attendance and sign_out_attendance:
            dt_the_day_morning_start_work_time = datetime.datetime.strptime(
                    "%s %s" % (date, sign_in_attendance.morning_start_work_time), DEFAULT_SERVER_DATETIME_FORMAT)
            dt_the_day_morning_end_work_time = datetime.datetime.strptime(
                    "%s %s" % (date, sign_in_attendance.morning_end_work_time), DEFAULT_SERVER_DATETIME_FORMAT)
            dt_the_day_afternoon_start_work_time = datetime.datetime.strptime(
                    "%s %s" % (date, sign_out_attendance.afternoon_start_work_time), DEFAULT_SERVER_DATETIME_FORMAT)
            dt_the_day_afternoon_end_work_time = datetime.datetime.strptime(
                    "%s %s" % (date, sign_out_attendance.afternoon_end_work_time), DEFAULT_SERVER_DATETIME_FORMAT)

            dt_sign_in_time = Datetime.from_string(sign_in_attendance.name) + datetime.timedelta(hours=8)
            dt_sign_out_time = Datetime.from_string(sign_out_attendance.name) + datetime.timedelta(hours=8)

            # morning first
            dt_cal_start = max(dt_the_day_morning_start_work_time, dt_sign_in_time)
            dt_cal_start = min(dt_cal_start, dt_the_day_morning_end_work_time)

            # dt_cal_end = min(dt_the_day_morning_end_work_time, dt_sign_out_time)
            # dt_cal_end = max(dt_cal_end, dt_the_day_morning_start_work_time)
            dt_cal_end = dt_the_day_morning_end_work_time
            work_duration = datetime.timedelta()
            if dt_cal_end > dt_cal_start:
                work_duration += dt_cal_end - dt_cal_start

            # then deal with afternoon
            # dt_cal_start = max(dt_the_day_afternoon_start_work_time, dt_sign_out_time)
            # dt_cal_start = min(dt_cal_start, dt_the_day_afternoon_end_work_time)
            dt_cal_start = dt_the_day_afternoon_start_work_time

            dt_cal_end = min(dt_the_day_afternoon_end_work_time, dt_sign_out_time)
            dt_cal_end = max(dt_cal_end, dt_the_day_afternoon_start_work_time)

            if dt_cal_end > dt_cal_start:
                work_duration += dt_cal_end - dt_cal_start

            return work_duration.seconds / 3600.0

    @api.multi
    def get_sign_in_attendance(self, date):
        self.ensure_one()

        Attendance = self.env["hr.attendance"].sudo()

        query_date_start = "%s %s" % (date, "0:0:0")
        query_date_start = UTC_String_From_TW_TZ(query_date_start)

        query_date_end = "%s %s" % (date, "23:59:59")
        query_date_end = UTC_String_From_TW_TZ(query_date_end)

        attendances = Attendance.search([("employee_id", "=", self.id),
                                         ("name", ">=", query_date_start),
                                         ("name", "<=", query_date_end),
                                         ("action", "=", "sign_in")])
        if attendances:
            attendance = attendances[0] if len(attendances) > 1 else attendances
            return attendance
        else:
            return None

    @api.multi
    def get_sign_out_attendance(self, date):
        self.ensure_one()

        Attendance = self.env["hr.attendance"].sudo()

        query_date_start = "%s %s" % (date, "0:0:0")
        query_date_start = UTC_String_From_TW_TZ(query_date_start)

        query_date_end = "%s %s" % (date, "23:59:59")
        query_date_end = UTC_String_From_TW_TZ(query_date_end)

        attendances = Attendance.search([("employee_id", "=", self.id),
                                         ("name", ">=", query_date_start),
                                         ("name", "<=", query_date_end),
                                         ("action", "=", "sign_out")])
        if attendances:
            attendance = attendances[0] if len(attendances) > 1 else attendances
            return attendance
        else:
            return None

    @api.multi
    def get_end_work_time_on(self, date=None):
        self.ensure_one()
        if not date:
            return None

        attendance = self.get_sign_out_attendance(date)

        return UTC_Datetime_To_TW_TZ(attendance.name) if attendance else None

    @api.multi
    def get_early_minutes_on(self, date=None):
        self.ensure_one()
        if not date:
            return None

        attendance = self.get_sign_out_attendance(date)
        if attendance:
            dt_action_time = UTC_Datetime_To_TW_TZ(attendance.name).time()
            dt_start_work_time = datetime.datetime.strptime(attendance.morning_start_work_time,
                                                            DEFAULT_SERVER_TIME_FORMAT).time()
            dt_morning_end_work_time = datetime.datetime.strptime(attendance.morning_end_work_time,
                                                                  DEFAULT_SERVER_TIME_FORMAT).time()
            dt_afternoon_start_work_time = datetime.datetime.strptime(attendance.afternoon_start_work_time,
                                                                      DEFAULT_SERVER_TIME_FORMAT).time()
            dt_afternoon_end_work_time = datetime.datetime.strptime(attendance.afternoon_end_work_time,
                                                                    DEFAULT_SERVER_TIME_FORMAT).time()
            dt_cal_start = dt_afternoon_end_work_time
            leaves = self.get_holiday_on(date).values()
            all_leaves = list()
            for l in leaves:
                all_leaves.extend(l)

            all_leaves = sorted(all_leaves, key=lambda l: l[0], reverse=True)
            for leave in all_leaves:
                if leave[1].time() >= dt_cal_start:
                    dt_cal_start = leave[0].time()
                    if dt_morning_end_work_time < dt_cal_start <= dt_afternoon_start_work_time:
                        dt_cal_start = dt_morning_end_work_time
                else:
                    break

            if dt_action_time < dt_cal_start:
                now = datetime.datetime.now()
                dt1 = datetime.datetime(now.year, now.month, now.day,
                                        hour=dt_action_time.hour,
                                        minute=dt_action_time.minute,
                                        second=dt_action_time.second)
                dt2 = datetime.datetime(now.year, now.month, now.day,
                                        hour=dt_cal_start.hour,
                                        minute=dt_cal_start.minute,
                                        second=dt_cal_start.second)

                return (dt2 - dt1).seconds / 60.0
                # return attendance.late_minutes if attendance else None

    @api.multi
    def get_late_minutes_on(self, date=None):
        self.ensure_one()
        if not date:
            return None

        attendance = self.get_sign_in_attendance(date)
        if attendance:
            dt_action_time = UTC_Datetime_To_TW_TZ(attendance.name).time()
            dt_start_work_time = datetime.datetime.strptime(attendance.morning_start_work_time,
                                                            DEFAULT_SERVER_TIME_FORMAT).time()
            dt_morning_end_work_time = datetime.datetime.strptime(attendance.morning_end_work_time,
                                                                  DEFAULT_SERVER_TIME_FORMAT).time()
            dt_afternoon_start_work_time = datetime.datetime.strptime(attendance.afternoon_start_work_time,
                                                                      DEFAULT_SERVER_TIME_FORMAT).time()
            dt_afternoon_end_work_time = datetime.datetime.strptime(attendance.afternoon_end_work_time,
                                                                    DEFAULT_SERVER_TIME_FORMAT).time()
            dt_cal_start = dt_start_work_time
            leaves = self.get_holiday_on(date).values()
            all_leaves = list()
            for l in leaves:
                all_leaves.extend(l)

            all_leaves = sorted(all_leaves, key=lambda l: l[0])
            for leave in all_leaves:
                if leave[0].time() <= dt_cal_start:
                    dt_cal_start = leave[1].time()
                    if dt_cal_start == dt_morning_end_work_time:
                        dt_cal_start = dt_afternoon_start_work_time
                else:
                    break

            if dt_action_time > dt_cal_start:
                now = datetime.datetime.now()
                dt1 = datetime.datetime(now.year, now.month, now.day,
                                        hour=dt_action_time.hour,
                                        minute=dt_action_time.minute,
                                        second=dt_action_time.second)
                dt2 = datetime.datetime(now.year, now.month, now.day,
                                        hour=dt_cal_start.hour,
                                        minute=dt_cal_start.minute,
                                        second=dt_cal_start.second)

                return (dt1 - dt2).seconds / 60.0
                # return attendance.late_minutes if attendance else None

    @api.multi
    def get_forget_card_on(self, date=None):
        self.ensure_one()
        if not date:
            return None

        Attendance = self.env["hr.attendance"].sudo()
        query_date_start = "%s %s" % (date, "0:0:0")
        query_date_start = UTC_String_From_TW_TZ(query_date_start)

        query_date_end = "%s %s" % (date, "23:59:59")
        query_date_end = UTC_String_From_TW_TZ(query_date_end)

        attendances = Attendance.search([("employee_id", "=", self.id),
                                         ("name", ">=", query_date_start),
                                         ("name", "<=", query_date_end),
                                         ("forget_card", "=", True)])
        forget_count = len(attendances) if attendances else 0
        in_attendance = self.get_sign_in_attendance(date)
        if not in_attendance:
            forget_count += 1
        out_attendance = self.get_sign_out_attendance(date)
        if not out_attendance:
            forget_count += 1
        return forget_count

    @api.multi
    def get_overtime_hours_on(self, date_from=None, date_to=None):
        self.ensure_one()
        if not all((date_from, date_to)):
            return None

        if self.responsibility:
            return 0

        Overtime = self.env["hr_sf.overtime"].sudo()

        # date_from = "%s %s" % (date_from, "0:0:0")
        # date_from = UTC_String_From_TW_TZ(date_from)
        #
        # date_to = "%s %s" % (date_to, "23:59:59")
        # date_to = UTC_String_From_TW_TZ(date_to)

        overtimes = Overtime.search([("date", ">=", date_from),
                                     ("date", "<=", date_to),
                                     ("employee_ids", "in", self.id),
                                     ("state", "=", "approved")])

        # TODO 这里还要检查有没有打卡记录

        if overtimes:
            duration = dict()
            duration['stage1'] = sum(o.duration_stage1 for o in overtimes)
            duration['stage2'] = sum(o.duration_stage2 for o in overtimes)
            duration['stage3'] = sum(o.duration_stage3 for o in overtimes)
            return duration
        else:
            return None

    @api.multi
    def get_attendance_detail_line(self, dt_date):
        self.ensure_one()
        if not isinstance(dt_date, datetime.date):
            return None

        OfficialHoliday = self.env["hr.official_holiday"]

        dt_str = Date.to_string(dt_date)

        overtime_durations = self.get_overtime_hours_on(date_from=dt_str, date_to=dt_str)
        if dt_date.weekday() in (5, 6) and not overtime_durations:
            return None

        line = dict()
        line['name'] = self.name
        line['emp_dep'] = self.department_id.name
        line['emp_code'] = self.internal_code
        line['date'] = dt_date.strftime(DEFAULT_SERVER_DATE_FORMAT)  # + " %A" Date.to_string(dt)

        start_work_time = self.get_start_work_time_on(dt_str)
        line["start_work_time"] = start_work_time.strftime(DEFAULT_SERVER_TIME_FORMAT) \
            if start_work_time else None

        end_work_time = self.get_end_work_time_on(dt_str)
        line["end_work_time"] = end_work_time.strftime(DEFAULT_SERVER_TIME_FORMAT) \
            if end_work_time else None

        late_minutes = self.get_late_minutes_on(dt_str)
        line["late_minutes"] = round(late_minutes, 2) if late_minutes else None

        early_minutes = self.get_early_minutes_on(dt_str)
        line["early_minutes"] = round(early_minutes, 2) if early_minutes else None

        work_duration = self.get_work_duration_on(dt_str)
        line["work_duration"] = round(work_duration, 2) if work_duration else None

        # overtime_durations = self.get_overtime_hours_on(date_from=dt_str, date_to=dt_str)

        if overtime_durations:
            line["overtime_stage1"] = overtime_durations.get("stage1", None)
            line["overtime_stage2"] = overtime_durations.get("stage2", None)
            line["overtime_stage3"] = overtime_durations.get("stage3", None)

        # line["overtime_hours"] = round(overtime_hours, 2)

        leaves = self.get_holiday_on(dt_str)
        line["holiday_detail"] = leaves

        all_leaves = list()
        if leaves:
            for l in leaves.values():
                all_leaves.extend(l)
        holiday_total = round(sum(l[2].seconds / 3600.0 for l in all_leaves), 2)
        line["holiday_total"] = holiday_total

        official_holiday = OfficialHoliday.get_official_holiday_on(dt_str)
        line["official_holiday"] = official_holiday

        absent = self.get_absent_on(dt_str)

        if leaves:
            line["summary"] = string.join(
                    set(leaves.keys() + ([absent] if absent else []) + ([official_holiday] if official_holiday else [])),
                    ",")
        else:
            line["summary"] = None

        if not official_holiday and holiday_total < 8.0:
            line["forget_card"] = self.get_forget_card_on(dt_str)
        else:
            line["forget_card"] = None
        return line
