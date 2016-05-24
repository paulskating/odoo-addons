# _*_ coding: utf-8 _*_
import xlwt
import datetime
import StringIO
import base64
from openerp import models, fields, api, _
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT


class ReportAttendanceDetailWizard(models.TransientModel):
    _inherit = "hr_sf.report_wizard_base"
    _name = "hr_sf.report_attendance_detail_wizard"

    @api.multi
    def action_OK(self):
        self.ensure_one()
        if self.export_as_xls:
            self.generate_xls()
            self.state = "step2"
            return self.next_step()
        else:
            data = self.get_input_values()
            return self.env['report'].get_action(self, 'hr_sf.report_attendance_detail', data=data)

    @api.multi
    def generate_xls(self):
        self.ensure_one()

        style0 = xlwt.easyxf('font: name Times New Roman, color-index red, bold on',
                             num_format_str='#,##0.00')
        style1 = xlwt.easyxf(num_format_str='D-MMM-YY')

        wb = xlwt.Workbook()
        ws = wb.add_sheet('A Test Sheet')

        ws.write(0, 0, 1234.56, style0)
        ws.write(1, 0, datetime.datetime.now(), style1)
        ws.write(2, 0, 1)
        ws.write(2, 1, 1)
        ws.write(2, 2, xlwt.Formula("A3+B3"))

        output = StringIO.StringIO()

        wb.save(output)

        self.xls_file = base64.standard_b64encode(output.getvalue())
        self.xls_file_name = _("出勤明细表")