# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from collections import OrderedDict
from datetime import timedelta


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    def create_invoices(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        for order in sale_orders.filtered(lambda x: not x.clx_invoice_policy_id):
            order._create_invoices(
                final=self.deduct_down_payments)
        if self.start_date and self.end_date:
            lines = self.env['sale.subscription.line'].search([
                ('so_line_id.order_id', 'in', sale_orders.ids),
            ])
            if not lines:
                raise UserError(_("You need to sale order for create a invoice!!"))
            advance_lines = lines.filtered(
                lambda sl: (sl.so_line_id.order_id.clx_invoice_policy_id.policy_type == 'advance'))
            advance_lines = advance_lines.filtered(lambda
                                                       x: x.invoice_start_date and x.invoice_start_date <= self.start_date)
            if not advance_lines:
                raise UserError(_("Invoice is created or posted Please check all invoices of this Customer"))
            partners = advance_lines.mapped('so_line_id').mapped('order_partner_id')
            month_count = len(OrderedDict(((self.start_date + timedelta(_)).strftime("%B-%Y"), 0) for _ in
                                          range((self.end_date - self.start_date).days)))
            for i in range(0, month_count):
                for partner in partners:
                    adv_lines = advance_lines.filtered(lambda x: x.so_line_id.order_partner_id.id == partner.id)
                    partner.with_context(generate_invoice_date_range=True, start_date=self.start_date,
                                         end_date=self.end_date,
                                         ).generate_advance_invoice(
                        adv_lines)
        else:
            count = 1
            for i in range(0, count):
                # filter sale order invoice policy advance and invoice creation based on sale order line
                advance_sale_orders_sol = sale_orders.filtered(
                    lambda x: x.clx_invoice_policy_id.policy_type == 'advance'
                              and (x.partner_id.child_invoice_selection == 'sol'
                                   or x.partner_id.invoice_selection == 'sol')
                )
                if advance_sale_orders_sol:
                    # advance_sale_orders_sol.with_context(invoice_section='sol')._create_invoices_wizard(
                    #     final=self.deduct_down_payments)
                    for order in advance_sale_orders_sol:
                        order.partner_id.with_context(create_invoice_from_wzrd=True, sol=True,
                                                      order=order.id).generate_invoice()

                # filter sale order invoice policy advance and invoice creation based on Category wise
                advance_sale_orders_categ = sale_orders.filtered(
                    lambda x: x.clx_invoice_policy_id.policy_type == 'advance'
                              and (
                                      x.partner_id.child_invoice_selection == 'prod_categ' or
                                      x.partner_id.invoice_selection == 'prod_categ')
                )
                if advance_sale_orders_categ:
                    for order in advance_sale_orders_categ:
                        order.partner_id.with_context(create_invoice_from_wzrd=True, order=order.id).generate_invoice()

                # filter sale order invoice policy arrears and invoice creation based on sale order line
                arrears_sale_orders_sol = sale_orders.filtered(
                    lambda x: x.clx_invoice_policy_id.policy_type == 'arrears'
                              and (x.partner_id.child_invoice_selection == 'sol'
                                   or x.partner_id.invoice_selection == 'sol')
                )
                if arrears_sale_orders_sol:
                    for order in arrears_sale_orders_sol:
                        order.partner_id.with_context(create_invoice_from_wzrd=True, sol=True,
                                                      order=order.id).generate_invoice()
                # filter sale order invoice policy arrears and invoice creation based on category
                arrears_sale_orders_categ = sale_orders.filtered(
                    lambda x: x.clx_invoice_policy_id.policy_type == 'arrears'
                              and (
                                      x.partner_id.child_invoice_selection == 'prod_categ'
                                      or x.partner_id.invoice_selection == 'prod_categ')
                )
                if arrears_sale_orders_categ:
                    for order in arrears_sale_orders_categ:
                        order.partner_id.with_context(create_invoice_from_wzrd=True, order=order.id).generate_invoice()
        if self._context.get('open_invoices', False):
            return sale_orders.action_view_invoice()
