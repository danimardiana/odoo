# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models, api, _
from itertools import groupby
from odoo.exceptions import AccessError, UserError
from odoo.tools import float_is_zero, float_compare
from dateutil.relativedelta import relativedelta


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    clx_invoice_policy_id = fields.Many2one(
        'clx.invoice.policy', string="Invoice Policy")

    def _action_confirm(self):
        """
        Create draft invoice when confirm the sale order.
        if sale order line start date is in current month.
        than create invoice current month.
        :return:
        """
        res = super(SaleOrder, self)._action_confirm()
        if self.is_ratio:
            return res
        lines = self.env['sale.subscription.line'].search([
            ('so_line_id', 'in', self.order_line.ids),
        ])
        current_month_start_day = fields.Date.today().replace(day=1)
        end_date = current_month_start_day + relativedelta(months=self.clx_invoice_policy_id.num_of_month + 1)
        end_date = end_date - relativedelta(days=1)
        so_lines = lines.filtered(lambda x: x.start_date and x.start_date < end_date)
        if lines:
            if self.partner_id.child_invoice_selection:
                if self.partner_id.child_invoice_selection == 'sol':
                    self.partner_id.with_context(cofirm_sale=True, sol=True).generate_advance_invoice(so_lines)
                else:
                    self.partner_id.with_context(cofirm_sale=True).generate_advance_invoice(so_lines)
            if not self.partner_id.child_invoice_selection and self.partner_id.invoice_selection:
                if self.partner_id.invoice_selection == 'sol':
                    self.partner_id.with_context(cofirm_sale=True, sol=True).generate_advance_invoice(so_lines)
                else:
                    self.partner_id.with_context(cofirm_sale=True).generate_advance_invoice(so_lines)
        return res

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super(SaleOrder, self).onchange_partner_id()
        if self.partner_id:
            self.clx_invoice_policy_id = self.partner_id.clx_invoice_policy_id.id if \
                self.partner_id.clx_invoice_policy_id else False

    @api.model
    def create(self, vals):
        so = super(SaleOrder, self).create(vals)
        if so.partner_id and not vals.get('clx_invoice_policy_id'):
            so.clx_invoice_policy_id = so.partner_id.clx_invoice_policy_id.id
        return so

    def _create_invoices_wizard(self, grouped=False, final=False):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        if not self.env['account.move'].check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except AccessError:
                return self.env['account.move']

        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        # 1) Create invoices.
        invoice_vals_list = []
        for order in self:
            pending_section = None

            # Invoice values.
            invoice_vals = order._prepare_invoice()
            order_line = order.order_line
            # Invoice line values (keep only necessary sections).
            if self._context.get('invoice_section'):
                order_line = self.env['sale.order.line']
                policy_month = order.clx_invoice_policy_id.num_of_month
                end_date = fields.Date.today().replace(day=1) + relativedelta(
                    months=policy_month + 1, days=-1)
                for line in order.order_line:
                    if line.start_date and line.start_date < end_date:
                        order_line += line
            for line in order_line:
                if line.display_type == 'line_section':
                    pending_section = line
                    continue
                if float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    continue
                if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final):
                    if pending_section:
                        invoice_vals['invoice_line_ids'].append((0, 0, pending_section._prepare_invoice_line()))
                        pending_section = None
                    invoice_vals['invoice_line_ids'].append((0, 0, line._prepare_invoice_line()))

            if not invoice_vals['invoice_line_ids']:
                raise UserError(_(
                    'There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise UserError(_(
                'There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

        moves = self.env['account.move'].sudo().with_context(default_type='out_invoice').create(invoice_vals_list)
        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        if final:
            moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
        for move in moves:
            move.message_post_with_view('mail.message_origin_link',
                                        values={'self': move, 'origin': move.line_ids.mapped('sale_line_ids.order_id')},
                                        subtype_id=self.env.ref('mail.mt_note').id
                                        )
        return moves
