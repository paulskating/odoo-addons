# _*_ coding: utf-8 _*_
import datetime
from collections import defaultdict
import string
from openerp import models, api, _
from openerp.fields import Date
from openerp.tools.misc import DEFAULT_SERVER_TIME_FORMAT
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT


class ReportAttendanceStatistics(models.AbstractModel):
    _name = "report.hr_sf.report_attendance_statistics"

    @api.multi
    def render_html(self, data=None):
        date_from = data.get("date_from", None)
        date_to = data.get("date_to", None)
        repeat_header = data.get("repeat_header", None)
        filter_by = data.get("filter_by", None)
        employee_ids = data.get("employee_ids", None)
        department_ids = data.get("department_ids", None)

        docargs = dict()
        docargs["emp_attendances"] = self.get_attendance_statistics(date_from, date_to, filter_by,
                                                                    employee_ids, department_ids)
        docargs["holiday_names"] = reduce(lambda s, e: s | set(e["holiday_detail"].keys()), docargs["emp_attendances"],
                                          set())
        docargs["date_from"] = date_from
        docargs["date_to"] = date_to
        docargs["repeat_header"] = repeat_header
        return self.env['report'].render('hr_sf.report_attendance_statistics', values=docargs)

    def get_attendance_statistics(self, date_from=None, date_to=None, filter_by=None, employee_ids=None,
                                  department_ids=None):
        CAL_START_TIME = datetime.datetime.now()
        print "开始计算出勤统计表:", CAL_START_TIME
        if any((date_from, date_to)) and not all((date_from, date_to)):
            return "miss date_from or date_to"

        if not date_from and not date_to:
            now = datetime.datetime.now()
            date_from = datetime.datetime(now.year, now.month, 1)
            date_to = datetime.datetime(date_from.year, date_from.month + 1, 1)
        elif date_from and date_to:
            date_from = Date.from_string(date_from)
            date_to = Date.from_string(date_to)

        Employee = self.env["hr.employee"].sudo()

        employee_search_domain = []
        if filter_by == "employee" and employee_ids:
            employee_search_domain.append(("id", "in", employee_ids))
        if filter_by == "department" and department_ids:
            employee_search_domain.append(("department_id", "in", department_ids))
        all_employees = Employee.search(employee_search_domain)
        all_employees = sorted(all_employees,
                               key=lambda e: (e.department_id.name if e.department_id else "", e.internal_code))

        emp_attendances_values = []
        for emp in all_employees:
            dt = date_from
            emp_lines = list()
            days = 0
            while dt <= date_to:
                line = emp.get_attendance_detail_line(dt)
                if line:
                    emp_lines.append(line)
                days += 1
                dt += datetime.timedelta(days=1)

            if emp_lines:
                emp_total_line = dict()
                emp_total_line["name"] = emp.name
                emp_total_line['emp_dep'] = emp.department_id.name if emp.department_id else ""
                emp_total_line['emp_code'] = emp.internal_code
                # emp_total_line['date'] = '小计'
                # emp_total_line['end_work_time'] = None
                # emp_total_line['start_work_time'] = None
                # emp_total_line['late_minutes'] = sum(l["late_minutes"] or 0 for l in emp_lines)
                # emp_total_line['early_minutes'] = sum(l["early_minutes"] or 0 for l in emp_lines)
                emp_total_line["work_duration"] = round(sum(l.get("work_duration", None) or 0 for l in emp_lines) / 8.0,
                                                        2)
                # emp_total_line["late_minutes"] = sum(l["late_minutes"] or 0 for l in emp_lines)

                emp_total_line["overtime_stage1"] = sum(l.get("overtime_stage1", None) or 0 for l in emp_lines)
                emp_total_line["overtime_stage2"] = sum(l.get("overtime_stage2", None) or 0 for l in emp_lines)
                emp_total_line["overtime_stage3"] = sum(l.get("overtime_stage3", None) or 0 for l in emp_lines)

                holiday_detail = defaultdict(lambda: 0)
                for line in emp_lines:
                    if line.get("holiday_detail", None):
                        for holiday in line["holiday_detail"]:
                            holiday_detail[holiday] += round(
                                    sum(h[2].seconds / 3600.0 for h in line["holiday_detail"][holiday]), 2)

                emp_total_line["holiday_detail"] = holiday_detail

                emp_total_line["holiday_total"] = sum(l["holiday_total"] or 0 for l in emp_lines)

                # emp_total_line["summary"] = string.join(set(l["summary"] for l in emp_lines))
                emp_total_line["forget_card"] = sum(l["forget_card"] or 0 for l in emp_lines)
                #
                emp_attendances_values.append(emp_total_line)

        CAL_END_TIME = datetime.datetime.now()
        print "结束时间:", CAL_END_TIME
        print "耗时:", CAL_END_TIME - CAL_START_TIME
        return emp_attendances_values
