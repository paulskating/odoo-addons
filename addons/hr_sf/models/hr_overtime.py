# _*_ coding: utf-8 _*_
import datetime

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
from openerp.exceptions import Warning
from openerp.tools.misc import DEFAULT_SERVER_TIME_FORMAT


class Overtime(models.Model):
    _inherit = "mail.thread"
    _name = "hr_sf.overtime"

    # _rec_name = "name"
    _order = "date desc"

    @api.multi
    def _def_department_id(self):
        employee = self.env["hr.employee"].search([("user_id", "=", self.env.user.id)])
        if employee:
            return employee[0].department_id

    name = fields.Char('Order Reference', default='/',
                       required=True, copy=False, readonly=True)

    type = fields.Selection([("night", "night"), ("holiday", "holiday")], required=True,
                            states={"confirmed": [("readonly", True)], "approved": [("readonly", True)]})

    work_content = fields.Text(states={"confirmed": [("readonly", True)], "approved": [("readonly", True)]})
    night_overtime_duration = fields.Selection([("0.5", "0.5"),
                                                ("1.0", "1.0"),
                                                ("1.5", "1.5"),
                                                ("2.0", "2.0"),
                                                ("2.5", "2.5"),
                                                ("3.0", "3.0")], states={"confirmed": [("readonly", True)],
                                                                         "approved": [("readonly", True)]},
                                               string="duration")
    # night_overtime_date_from = fields.Datetime(requried=True)
    # night_overtime_date_to = fields.Datetime(requried=True)

    date = fields.Date(required=True, states={"confirmed": [("readonly", True)], "approved": [("readonly", True)]})
    holiday_overtime_duration = fields.Selection([("1", "1"),
                                                  ("2", "2"),
                                                  ("3", "3"),
                                                  ("4", "4"),
                                                  ("5", "5"),
                                                  ("6", "6"),
                                                  ("7", "7"),
                                                  ("8", "8")],
                                                 states={"confirmed": [("readonly", True)],
                                                         "approved": [("readonly", True)]},
                                                 string="duration")

    department_id = fields.Many2one("hr.department", default=_def_department_id, required=True,
                                    states={"confirmed": [("readonly", True)], "approved": [("readonly", True)]})
    employee_ids = fields.Many2many("hr.employee",
                                    states={"confirmed": [("readonly", True)], "approved": [("readonly", True)]})

    # related_user_ids = fields.Many2one("res.users")
    employees_allowed_to_see = fields.Many2many("hr.employee", relation="hr_sf_overtime_allow_employee_to_see")

    duration_stage1 = fields.Float(compute="_compute_duration", store=True, help="第一段加班时数，以小时为单位。")
    duration_stage2 = fields.Float(compute="_compute_duration", store=True, help="第二段加班时数，以小时为单位。")
    duration_stage3 = fields.Float(compute="_compute_duration", store=True, help="第三段加班时数，以小时为单位。")
    state = fields.Selection([("draft", "Draft"),
                              ("confirmed", "Confirmed"),
                              ("approved", "Approved")], default="draft")

    _sql_constraints = [
        ('name_uniq', 'unique(name, company_id)', 'Order Reference must be unique per Company!'),
    ]

    # @api.constrains("night_overtime_date_from", "night_overtime_date_to")
    # @api.multi
    # def _constrains_date(self):
    #     self.ensure_one()
    #     if self.night_overtime_date_from >= self.night_overtime_date_to:
    #         raise ValidationError(_("date to must later then date from"))

    @api.depends("type", "date", "night_overtime_duration", "holiday_overtime_duration")
    @api.multi
    def _compute_duration(self):
        ConfigParameter = self.env['ir.config_parameter'].sudo()
        night_overtime_start_time = ConfigParameter.get_param('night_overtime_start_time')
        night_overtime_middle_time = ConfigParameter.get_param('night_overtime_middle_time')
        night_overtime_end_time = ConfigParameter.get_param('night_overtime_end_time')

        for overtime in self:
            if overtime.type == "holiday":
                overtime.duration_stage1 = 0
                overtime.duration_stage2 = 0
                overtime.duration_stage3 = float(overtime.holiday_overtime_duration)
            elif overtime.type == "night":
                dt_start = datetime.datetime.strptime(night_overtime_start_time, DEFAULT_SERVER_TIME_FORMAT)
                dt_middle = datetime.datetime.strptime(night_overtime_middle_time, DEFAULT_SERVER_TIME_FORMAT)
                dt_end = datetime.datetime.strptime(night_overtime_end_time, DEFAULT_SERVER_TIME_FORMAT)
                stage1_max = (dt_middle - dt_start).seconds / 3600.0
                stage2_max = (dt_end - dt_middle).seconds / 3600.0
                night_overtime_duration = float(overtime.night_overtime_duration)
                if night_overtime_duration <= stage1_max:
                    overtime.duration_stage1 = night_overtime_duration
                    overtime.duration_stage2 = 0
                    overtime.duration_stage3 = 0
                elif stage1_max < night_overtime_duration <= stage1_max + stage2_max:
                    overtime.duration_stage1 = stage1_max
                    overtime.duration_stage2 = night_overtime_duration - stage1_max
                    overtime.duration_stage3 = 0
                else:
                    overtime.duration_stage1 = stage1_max
                    overtime.duration_stage2 = stage2_max
                    overtime.duration_stage3 = 0

    # @api.onchange("employee_ids")
    # @api.multi
    # def _onchange_employee_ids(self):
    #     for overtime in self:
    #         overtime.related_user_ids = overtime.employee_ids.mapped("user_id")

    @api.multi
    def action_confirm(self):
        self.ensure_one()
        if self.department_id and \
                self.department_id.manager_id and \
                self.department_id.manager_id.user_id:
            self.message_follower_ids += self.department_id.manager_id.user_id.partner_id
        managers = self.env.ref("base.group_hr_manager").users.mapped("partner_id")
        self.message_follower_ids += managers

        mail_values = {'body': _('<p>新的加班单待审批。</p>'), 'partner_ids': self.message_follower_ids.ids}
        self.message_post(**mail_values)

        self.state = "confirmed"

    @api.multi
    def action_approve(self):
        self.ensure_one()
        self.state = "approved"

    @api.multi
    def action_reset_to_draft(self):
        self.ensure_one()
        self.state = "draft"

    @api.multi
    def unlink(self):
        for overtime in self:
            if overtime.state != "draft":
                raise Warning(_("Only draft overtimes can be deleted!"))
        super(Overtime, self).unlink()

    @api.onchange("department_id")
    @api.multi
    def _onchange_department_id(self):
        self.ensure_one()
        value = dict()
        if self.department_id:
            dep = self.department_id
            employees = None
            while dep:
                if dep.manager_id:
                    if not employees:
                        employees = dep.manager_id
                    else:
                        employees += dep.manager_id
                dep = dep.parent_id
            self.employees_allowed_to_see = employees
            domain = [("department_id", "=", self.department_id.id)]
            value["domain"] = dict()
            value["domain"]["employee_ids"] = domain
        return value

    @api.onchange("type")
    @api.multi
    def _onchange_type(self):
        self.ensure_one()
        if self.type == "night":
            self.holiday_overtime_duration = None
        elif self.type == "holiday":
            self.night_overtime_duration = None

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].get('overtime.order') or '/'
        return super(Overtime, self).create(vals)
