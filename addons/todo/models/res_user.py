from openerp import models,fields,api
from openerp.exceptions import UserError

class ResUser(models.Model):
    _inherit="res.users"
    _name = "res.users"

    todo_ids=fields.One2many("todo.thing","user_id")

    partner_id = fields.Many2one("res.partner",help="abc")

    @api.multi
    def action_reset_password(self):
        raise UserError("Not allow")
        super(ResUser, self).action_reset_password()


