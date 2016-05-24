# _*_ coding: utf-8 _*_
import csv
import base64
import datetime
import itertools
import string
from collections import defaultdict

from openerp.fields import Datetime
from openerp.fields import Date
from openerp.http import route
from openerp.http import Controller
from openerp.http import request
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools import DEFAULT_SERVER_TIME_FORMAT
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp import _
from ..tools.TimeZoneHelper import UTC_Datetime_To_TW_TZ


class HR_SF_Controller(Controller):
    @route("/hr_sf/attendance", auth="public", methods=["GET", "POST"])
    def index(self, **kwargs):
        method = request.httprequest.method
        if method == "GET":
            return request.render("hr_sf.attendance_index")
        elif method == "POST":
            Attendance = request.env["hr.attendance"].sudo()
            Employee = request.env["hr.employee"].sudo()
            UploadLog = request.env["hr_sf.attendance_upload_log"].sudo()

            try:
                upload_file = kwargs.get("upload_file", None)
                source = kwargs.get("source", None)
                if upload_file is None:
                    raise Exception("can not get upload file from http post data")
                upload_file_content = upload_file.stream.read()
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(upload_file_content, delimiters=',\t')
                rows = csv.reader(upload_file_content.splitlines(), dialect=dialect)

                upload_log = None
                if rows:
                    base64_file = base64.standard_b64encode(upload_file_content)
                    upload_log = UploadLog.create({"upload_file": base64_file, "file_name": upload_file.filename,
                                                   "date": Datetime.now(), "source": source})
                upload_log_id = upload_log.id

                employees = Employee.search([])
                employee_ids = dict(employees.mapped(lambda r: (r.internal_code, r.id)))

                line_number = 0
                values = []
                for row in rows:
                    code, name, year, month, day, hour, minute = row[0:7]
                    location = str(int(row[7]))

                    dt_str = "%s-%s-%s %s:%s:00" % (year, month, day, hour, minute)
                    dt = Datetime.from_string(dt_str)
                    dt = dt - datetime.timedelta(hours=8)
                    odoo_dt_str = Datetime.to_string(dt)

                    exist_count = Attendance.search_count([("code", "=", code), ("name", "=", odoo_dt_str)])
                    if exist_count <= 0:
                        emp_id = employee_ids.get(code, None)
                        if emp_id is not None:
                            # Attendance.create({"employee_id": emp_id, "name": odoo_dt_str, "location": location,
                            #                    "action": "action", "upload_log_id": upload_log_id})
                            values.append({"employee_id": emp_id, "name": odoo_dt_str, "location": location,
                                           "action": "action", "upload_log_id": upload_log_id,
                                           "forget_card": False})
                        else:
                            raise Exception("error in line:%d,employee with code:%s not found" % (line_number, code))
                    line_number += 1

                for value in values:
                    Attendance.create(value)

                return request.render("hr_sf.attendance_upload_finish", {"import_count": len(values)})
            except Exception, e:
                request.env.cr.rollback()
                return e.message or e.value

    @route("/hr_sf/report/per_location", auth="public", methods=["GET"])
    def attendance_per_location(self, date=None, location=None):
        if not date:
            date = Date.today()

        dt_from = datetime.datetime.strptime("%s 00:00:00" % date, DEFAULT_SERVER_DATETIME_FORMAT) - datetime.timedelta(
                hours=8)
        dt_to = datetime.datetime.strptime("%s 23:59:59" % date, DEFAULT_SERVER_DATETIME_FORMAT) - datetime.timedelta(
                hours=8)

        if not location:
            location = "1"

        Attendance = request.env["hr.attendance"].sudo()
        Employee = request.env["hr.employee"].sudo()
        values = {}

        domain = []
        if date:
            domain.append(("name", ">=", Datetime.to_string(dt_from)))
            domain.append(("name", "<=", Datetime.to_string(dt_to)))

        # if location:
        #     domain.append(("location", "=", location))

        all_employees = Employee.search([])

        emp_attendances_values = []
        for emp in all_employees:
            attendance = dict()
            attendance["name"] = emp.name
            attendance["dep"] = emp.department_id.name

            records = Attendance.search(domain + [("employee_id", "=", emp.id)],
                                        order="name")
            if records and records[-1].location:
                latest_rec = records[-1]
                attendance["state"] = "打卡"

                dt = UTC_Datetime_To_TW_TZ(latest_rec.name)
                date_part = dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
                time_part = dt.strftime(DEFAULT_SERVER_TIME_FORMAT)
                attendance["date"] = date_part
                attendance["time"] = time_part
                attendance["location"] = latest_rec.location
            else:
                attendance["state"] = "未打卡"
                attendance["date"] = None
                attendance["time"] = None
                attendance["location"] = None

            leave_time = emp.get_holiday_on(date)
            attendance["leave"] = string.join(leave_time.keys(), ",") if leave_time else None

            emp_attendances_values.append(attendance)

        # attendance_grouped_by_location = itertools.groupby(emp_attendances_values, key=lambda a: a["location"])
        attendances = defaultdict(lambda: list())
        for attendance in emp_attendances_values:
            attendances[attendance["location"]].append(attendance)  # or _("not attended")

        print_time = UTC_Datetime_To_TW_TZ(Datetime.now())
        values["print_time"] = Datetime.to_string(print_time)

        values["date"] = date
        values["location"] = location
        values["emp_attendances"] = attendances
        keys = sorted(attendances.keys())
        if None in keys:
            keys.remove(None)
            keys.append(None)
        values["attendance_keys"] = keys
        values["action_count"] = len(filter(lambda a: a.get("date", None), emp_attendances_values))
        values["un_action_count"] = len(filter(lambda a: not a.get("date", None), emp_attendances_values))

        return request.render("hr_sf.attendance_per_location", values)

        # @route("/hr_sf/report/attendance_detail", auth="public", methods=["GET"])
        # def attendance_detail(self, date_from=None, date_to=None):
        #     CAL_START_TIME = datetime.datetime.now()
        #     print "开始计算出勤明细表:", CAL_START_TIME
        #     if any((date_from, date_to)) and not all((date_from, date_to)):
        #         return "miss date_from or date_to"
        #
        #     if not date_from and not date_to:
        #         now = datetime.datetime.now()
        #         date_from = datetime.datetime(now.year, now.month, 1)
        #         date_to = datetime.datetime(date_from.year, date_from.month + 1, 1)
        #     elif date_from and date_to:
        #         date_from = Date.from_string(date_from)
        #         date_to = Date.from_string(date_to)
        #
        #     Employee = request.env["hr.employee"].sudo()
        #
        #     values = dict()
        #     emp_attendances_values = []
        #
        #     all_employees = Employee.search([])
        #     for emp in all_employees:
        #         dt = date_from
        #         while dt <= date_to:
        #             dt_str = Date.to_string(dt)
        #
        #             overtime_hours = emp.get_overtime_hours_on(date_from=dt_str, date_to=dt_str)
        #             if dt.weekday() in (5, 6) and (emp.responsibility or not overtime_hours):
        #                 dt += datetime.timedelta(days=1)
        #                 continue
        #
        #             line = dict()
        #             line['name'] = emp.name
        #             line['emp_dep'] = emp.department_id.name
        #             line['emp_code'] = emp.internal_code
        #             line['date'] = dt.strftime(DEFAULT_SERVER_DATE_FORMAT + " %A")  # Date.to_string(dt)
        #
        #             start_work_time = emp.get_start_work_time_on(dt_str)
        #             line["start_work_time"] = start_work_time.strftime(DEFAULT_SERVER_TIME_FORMAT) \
        #                 if start_work_time else None
        #
        #             end_work_time = emp.get_end_work_time_on(dt_str)
        #             line["end_work_time"] = end_work_time.strftime(DEFAULT_SERVER_TIME_FORMAT) \
        #                 if end_work_time else None
        #
        #             late_minutes = emp.get_late_minutes_on(dt_str)
        #             line["late_minutes"] = round(late_minutes, 2) if late_minutes else None
        #
        #             early_minutes = emp.get_early_minutes_on(dt_str)
        #             line["early_minutes"] = round(early_minutes, 2) if early_minutes else None
        #
        #             line["overtime_hours"] = round(overtime_hours, 2)
        #
        #             leaves = emp.get_holiday_on(dt_str)
        #             line["holiday_total"] = sum(l.seconds / 3600.0 for l in leaves.values())
        #             line["summary"] = string.join(leaves.keys(), ",")
        #             line["forget_card"] = emp.get_forget_card_on(dt_str)
        #
        #             emp_attendances_values.append(line)
        #             dt += datetime.timedelta(days=1)
        #
        #     values["emp_attendances"] = emp_attendances_values
        #     CAL_END_TIME = datetime.datetime.now()
        #     print "结束时间:", CAL_END_TIME
        #     print "耗时:", CAL_END_TIME - CAL_START_TIME
        #     return request.render("hr_sf.attendance_detail_webpage", values)
