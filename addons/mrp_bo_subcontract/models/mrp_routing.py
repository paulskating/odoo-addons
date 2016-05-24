# _*_ coding: utf-8 _*_
from openerp import models, fields, api


class Routing(models.Model):
    _inherit = "mrp.routing"

    is_create_picking = fields.Boolean(string=u'成品入库单',
                                       help=u'勾选则系统自动生成成品入库单，成品入库单入库时候，系统自动将MO报工。')
    # partner_id = fields.Many2one('res.partner', string=u'外协商', domain="[('supplier','=',True)]",
    #                              help=u'如果选择了外协商，成品入库单入库完成后，系统自动创建一张待开发票的成品入库单（外协入库单）。'),
    picking_type_id = fields.Many2one("stock.picking.type", string=u"单据类型")
