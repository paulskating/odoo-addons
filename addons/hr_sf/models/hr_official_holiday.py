# _*_ coding: utf-8 _*_
import datetime
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
from openerp.fields import Date


class OfficialHoliday(models.Model):
    _name = "hr.official_holiday"
    _rec_name = "name"

    name = fields.Char(required=True, copy=False)
    date_from = fields.Date(required=True)
    date_to = fields.Date()
    multi_days = fields.Boolean()

    @api.constrains("date_from", "date_to", "multi_days")
    @api.multi
    def _constraint_date(self):
        for holiday in self:
            if holiday.multi_days:
                if holiday.date_to <= holiday.date_from:
                    raise ValidationError(_("date_to must greater then date_from"))

    _sql_constraints = [
        ('official_holiday_name_uniq', 'unique(name)', 'The name of the official holiday must be unique!'),
    ]

    @api.model
    def get_official_holiday_on(self, date):
        domain = [("date_from", "=", date), ("multi_days", "=", False)]
        holiday = self.search(domain)
        if holiday:
            holiday = holiday[0]
            return holiday.name

        domain = [("date_from", "<=", date), ("date_to", ">=", date), ("multi_days", "=", True)]
        holiday = self.search(domain)
        if holiday:
            holiday = holiday[0]
            return holiday.name
