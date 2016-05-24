# _*_ coding: utf-8 _*_
from openerp import models, fields, api, _
from openerp.exceptions import Warning


class Procurement(models.Model):
    _inherit = "procurement.rule"

    @api.model
    def _get_action(self):
        return [('subcontract', _('Subcontract'))] + super(Procurement, self)._get_action()


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    subcontract_order_id = fields.Many2one("mrp.subcontract")
    subcontract_order_line_id = fields.Many2one("mrp.subcontract.order.line")

    @api.model
    def _run(self, procurement):
        if procurement.rule_id and procurement.rule_id.action == 'subcontract':
            # make a subcontract order for the procurement
            return procurement.make_subcontract_order()[procurement.id]
        return super(ProcurementOrder, self)._run(procurement)

    @api.multi
    def make_subcontract_order(self):
        """ Make Manufacturing(subcontract) order from procurement
        @return: New created Subcontract Orders procurement wise
        """
        res = {}
        sub_order = None
        sub_line = None
        pass_ids = []
        linked_po_ids = []
        sum_po_line_ids = []
        company = self.env.user.company_id
        Subcontract = self.env['mrp.subcontract']
        SubcontractLine = self.env['mrp.subcontract.order.line']

        for procurement in self:
            if not procurement.check_bom_exists():
                res[procurement.id] = False
                self.message_post(body=_("No BoM exists for this product!"))
                continue

            ctx_company = dict(force_company=procurement.company_id.id)
            partner = self.with_context(ctx_company)._get_product_supplier(procurement)

            if not partner:
                res[procurement.id] = False
                self.message_post(
                        body=_('There is no supplier associated to product %s') % (procurement.product_id.name))
                continue

            schedule_date = self._get_purchase_schedule_date(procurement, company)
            purchase_date = self._get_purchase_order_date(procurement, company, schedule_date)
            line_vals = self.with_context(ctx_company)._get_po_line_values_from_proc(procurement, partner, company,
                                                                                     schedule_date)

            # look for any other draft PO for the same supplier, to attach the new line on instead of creating a new draft one
            available_draft_sub_ids = Subcontract.search([
                ('partner_id', '=', partner.id),
                ('state', '=', 'draft')])

            if available_draft_sub_ids:
                sub_order = available_draft_sub_ids[0]
                # po_to_update = {'origin': ', '.join(filter(None, set([po_rec.origin, procurement.origin])))}
                # if the product has to be ordered earlier those in the existing PO, we replace the purchase date on the order to avoid ordering it too late
                # if datetime.strptime(po_rec.date_order, DEFAULT_SERVER_DATETIME_FORMAT) > purchase_date:
                #     po_to_update.update({'date_order': purchase_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
                # po_obj.write(cr, uid, [po_id], po_to_update, context=context)
                # look for any other PO line in the selected PO with same product and UoM to sum quantities instead of creating a new po line
                available_sub_line_ids = sub_order.line_ids.filtered(
                        lambda l: l.product_id == procurement.product_id)
                # po_line_obj.search(cr, uid, [('order_id', '=', po_id), ('product_id', '=', line_vals['product_id']), ('product_uom', '=', line_vals['product_uom'])], context=context)
                if available_sub_line_ids:
                    available_sub_line_ids[0].product_uom_qty += procurement.product_qty
                    self.message_post(body=_("Quantity added in existing Subcontract Order Line"))
                    sub_line = available_sub_line_ids[0]
                else:
                    sub_line = SubcontractLine.create({"order_id": sub_order.id,
                                            "product_id": procurement.product_id.id,
                                            "product_uom_qty": procurement.product_qty})
            else:
                vals = dict()
                vals["origin"] = procurement.origin
                vals["order_date"] = purchase_date
                sub_order = Subcontract.create(vals)
                sub_line = SubcontractLine.create({"order_id": sub_order.id,
                                            "product_id": procurement.product_id.id,
                                            "product_uom_qty": procurement.product_qty})

            res[procurement.id] = sub_line.id
            procurement.subcontract_order_line_id = sub_line
            procurement.subcontract_order_id = sub_order

        return res

    @api.model
    def _check(self, procurement):
        if procurement.rule_id and procurement.rule_id.action == 'subcontract':
            if procurement.subcontract_order_id and procurement.subcontract_order_id.state == 'done':  # TOCHECK: no better method?
                return True
        return super(ProcurementOrder, self)._check(procurement)

    @api.model
    def propagate_cancel(self, procurement):
        if procurement.rule_id and procurement.rule_id.action == 'subcontract' and procurement.subcontract_order_line_id:
            raise Warning(_("已经有产生了托工单明细行了,还未开发取消托工单的功能。"))
        return super(ProcurementOrder, self).propagate_cancel(procurement)


        # @api.multi
        # def make_subcontract_order(self):
        #     Subcontract = self.env["mrp.subcontract"]
        #
        #     res = dict()
        #     for procurement in self:
        #         if procurement.check_bom_exists():
        #             vals = procurement._prepare_subcontract_order_vals()
        #             subcontract_order = Subcontract.sudo().with_context(
        #                     {"force_company": procurement.company_id.id}).create(vals)
        #             res[procurement.id] = subcontract_order.id
        #             procurement.subcontract_order_id = subcontract_order
        #             procurement.subcontract_order_create_note()
        #             # subcontract_order.action_compute(cr, uid, [produce_id], properties=[x.id for x in procurement.property_ids])
        #             # subcontract_order.signal_workflow(cr, uid, [produce_id], 'button_confirm')
        #         else:
        #             res[procurement.id] = False
        #             self.message_post(procurement.ids, body=_("No BoM exists for this product!"))
        #     return res

        # @api.multi
        # def make_subcontract_order(self):
        #     Bom = self.env["mrp.bom"]
        #     ProductLine = self.env["purchase.order.line"]
        #     for proc in self:
        #         res = proc.make_po()
        #         if res:
        #             bom_id = Bom.sudo().with_context({"company_id": self.company_id.id})._bom_find(
        #                     product_id=self.product_id.id,
        #                     properties=self.property_ids.ids)
        #             if bom_id:
        #                 line = ProductLine.browse(res[proc.id])
        #                 if line:
        #                     line.write({"bom_id": bom_id})
        #     return res

        # @api.model
        # def create_procurement_purchase_order(self, procurement, po_vals, line_vals):
        #     """Create the purchase order from the procurement, using
        #        the provided field values, after adding the given purchase
        #        order line in the purchase order.
        #
        #        :params procurement: the procurement object generating the purchase order
        #        :params dict po_vals: field values for the new purchase order (the
        #                              ``order_line`` field will be overwritten with one
        #                              single line, as passed in ``line_vals``).
        #        :params dict line_vals: field values of the single purchase order line that
        #                                the purchase order will contain.
        #        :return: id of the newly created purchase order
        #        :rtype: int
        #     """
        #     PurchaseOrder = self.env["purchase.order"]
        #     po_vals.update({'order_line': [(0, 0, line_vals)]})
        #     po_vals["is_subcontract"] = True
        #     return PurchaseOrder.create(po_vals)

    @api.multi
    def _prepare_subcontract_order_vals(self):
        self.ensure_one()

        Bom = self.env["mrp.bom"]

        vals = dict()
        vals["product_id"] = self.product_id.id
        vals["origin"] = self.origin

        if self.bom_id:
            bom_id = self.bom_id.id
        else:
            bom = Bom.sudo().with_context({"company_id": self.company_id.id})._bom_find(
                    product_id=self.product_id.id,
                    properties=self.property_ids.ids)
            bom_id = bom[0].id if bom else None
        vals["bom_id"] = bom_id
        return vals

        # @api.multi
        # def subcontract_order_create_note(self):
        #     pass
