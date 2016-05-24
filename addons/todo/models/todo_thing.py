from openerp import models, fields, api


class TodoThing(models.Model):
    _name = "todo.thing"

    content = fields.Char(default="No Conytent")
    field_Boolean = fields.Boolean()
    field_Integer = fields.Integer()
    field_Float = fields.Float()
    field_Text = fields.Text()
    field_Selection = fields.Selection([("One", "One"),
                                        ("Two", "Two")])
    field_Html = fields.Html()
    field_Date = fields.Date()
    field_Datetime = fields.Datetime()

    user_id = fields.Many2one("res.users",
                              string="User",
                              required=True,
                              default=lambda self: self.env.user,
                              ondelete="cascade")

    email = fields.Char(compute="_compute_email", store=True)

    @api.depends("user_id","user_id.login")
    @api.multi
    def _compute_email(self):
        self.ensure_one()

        self.email = self.user_id.login

    phone = fields.Char()

    @api.onchange("user_id")
    @api.multi
    def _onchange_phone(self):
        self.ensure_one()
        self.phone = self.user_id.phone

    fax = fields.Char(related="user_id.fax")

    tag_ids = fields.Many2many("todo.tag")

    order_id = fields.Reference([("sale.order", "Sale order"),
                                 ("purchase.order", "Purchase Order")],
                                string="Order")

    @api.multi
    def action_fun1(self):
        self.ensure_one()

        str1 = "abc"
        str2 = str1 * 3
        self.content = str2

    @api.onchange("field_Boolean")
    def _onchange_field_Boolean(self):
        self.ensure_one()
        self.content = "_onchange_field_Boolean"
