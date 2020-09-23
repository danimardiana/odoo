# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.


from odoo.exceptions import AccessError

from odoo import models, fields, api


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    invoice_on = fields.Boolean(string="Invoice on")
    invoice_selection = fields.Selection([
        ('prod_categ', 'Product Category'),
        ('sol', 'Sale Order Line')
    ], string="Display on", default="prod_categ")
    is_advanced = fields.Boolean(string="Advanced?")

    @api.model
    def default_get(self, fields):
        vals = super(SaleAdvancePaymentInv, self).default_get(fields)
        if 'is_advanced' in fields:
            sos = self.env['sale.order'].browse(
                self._context.get('active_ids', [])
            )
            vals['is_advanced'] = all([
                s.clx_invoice_policy_id.policy_type == 'advance' for s in sos
            ])
        return vals

    def create_invoices(self):
        if not self.invoice_selection:
            return super(SaleAdvancePaymentInv, self).create_invoices()
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        for order in sale_orders.filtered(lambda x: not x.clx_invoice_policy_id):
            order._create_invoices(
                final=self.deduct_down_payments)
        if self.invoice_selection and sale_orders.filtered(lambda x: x.clx_invoice_policy_id):
            if self.invoice_selection == 'sol':
                sale_orders.with_context(invoice_section='sol')._create_invoices_wizard(
                    final=self.deduct_down_payments)
            if self.invoice_selection == 'prod_categ':
                act_move = self.env['account.move']
                if not act_move.check_access_rights('create', False):
                    try:
                        self.check_access_rights('write')
                        self.check_access_rule('write')
                    except AccessError:
                        return act_move
                for order in sale_orders.filtered(lambda x: x.clx_invoice_policy_id):
                    order.partner_id.with_context(create_invoice_from_wzrd=True, order=order.id).generate_invoice()
        if self._context.get('open_invoices', False):
            return sale_orders.action_view_invoice()
