# _*_ coding: utf-8 _*_
from openerp import models, fields


class AttendanceUploadLog(models.Model):
    _name = "hr_sf.attendance_upload_log"

    attendance_ids = fields.One2many("hr.attendance", "upload_log_id", string="Attendance records")
    upload_file = fields.Binary()
    file_name = fields.Char()
    source = fields.Selection(
            [("manual", "Manual - from web page."), ("automatic", "Automatic - from C# program.")])
    date = fields.Datetime()
