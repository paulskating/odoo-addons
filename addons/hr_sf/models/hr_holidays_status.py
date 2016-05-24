# _*_ coding: utf-8 _*_
from openerp import models, fields, api, _
from openerp.exceptions import Warning

class HolidayStatus(models.Model):
    _inherit = "hr.holidays.status"

    @api.multi
    def unlink(self):
        for holiday in self:
            xml_id = holiday.get_external_id()
            if "hr_sf.absent_holidays_status" in xml_id.values():
                raise Warning(_("do not delete this"))
