# _*_ coding:utf-8 _*_
from openerp import models, fields, api
from openerp.exceptions import UserError


class ResUsers(models.Model):

    _inherit = "res.users"

    todo_ids = fields.One2many("todo.thing", "user_id")

    partner_id = fields.Many2one('res.partner', help='word')

    @api.multi
    def action_reset_password(self):
        pass
        print('action_reset_password  adas')
        raise UserError("not allow")


