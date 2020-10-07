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
        # filter sale order invoice policy advance and invoice creation based on sale order line
        advance_sale_orders_sol = sale_orders.filtered(lambda x: x.clx_invoice_policy_id.policy_type == 'advance'
                                                                 and x.partner_id.invoice_selection == 'sol'
                                                       )
        if advance_sale_orders_sol:
            # advance_sale_orders_sol.with_context(invoice_section='sol')._create_invoices_wizard(
            #     final=self.deduct_down_payments)
            for order in advance_sale_orders_sol:
                order.partner_id.with_context(create_invoice_from_wzrd=True, sol=True,
                                              order=order.id).generate_invoice()

        # filter sale order invoice policy advance and invoice creation based on Category wise
        advance_sale_orders_categ = sale_orders.filtered(lambda x: x.clx_invoice_policy_id.policy_type == 'advance'
                                                                   and x.partner_id.invoice_selection == 'prod_categ'
                                                         )
        if advance_sale_orders_categ:
            for order in advance_sale_orders_categ:
                order.partner_id.with_context(create_invoice_from_wzrd=True, order=order.id).generate_invoice()

        # filter sale order invoice policy arrears and invoice creation based on sale order line
        arrears_sale_orders_sol = sale_orders.filtered(lambda x: x.clx_invoice_policy_id.policy_type == 'arrears'
                                                                 and x.partner_id.invoice_selection == 'sol'
                                                       )
        if arrears_sale_orders_sol:
            for order in arrears_sale_orders_sol:
                order.partner_id.with_context(create_invoice_from_wzrd=True, sol=True,
                                              order=order.id).generate_invoice()
        # filter sale order invoice policy arrears and invoice creation based on category
        arrears_sale_orders_categ = sale_orders.filtered(lambda x: x.clx_invoice_policy_id.policy_type == 'arrears'
                                                                   and x.partner_id.invoice_selection == 'prod_categ'
                                                         )
        if arrears_sale_orders_categ:
            for order in arrears_sale_orders_categ:
                order.partner_id.with_context(create_invoice_from_wzrd=True, order=order.id).generate_invoice()
        if self._context.get('open_invoices', False):
            return sale_orders.action_view_invoice()
