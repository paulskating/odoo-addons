from openerp import models, fields, api

class TodoTag(models.Model):
    _name="todo.tag"
    name=fields.Char()

    todo_thing_ids = fields.Many2many("todo.thing",
                                      relation="todo_tag_todo_thing_rel")

