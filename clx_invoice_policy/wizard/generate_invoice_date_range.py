# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.


from odoo import models, fields, api, _
from odoo.exceptions import UserError


class GenerateInvoiceDateRange(models.TransientModel):
    _name = "generate.invoice.date.range"

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    regenerate_cancel_invoice = fields.Boolean('Regenerate Cancel Invoices')

    @api.onchange('start_date', 'end_date')
    def onchange_date_validation(self):
        if self.start_date and self.end_date and \
                self.start_date >= self.end_date:
            raise UserError(_("Invalid date range."))

    def generate_invoice(self):
        partner_id = self.env['res.partner'].search([('id', '=', self._context.get('active_id'))])
        if partner_id:
            lines = self.env['sale.subscription.line'].search([
                ('so_line_id.order_id.partner_id', 'child_of', partner_id.id),
                ('so_line_id.order_id.state', 'in', ('sale', 'done')),
            ])
            if not lines:
                raise UserError(_("You need to sale order for create a invoice!!"))
            so_lines = lines.filtered(lambda x: x.invoice_start_date and x.invoice_start_date <= self.start_date)
            if not so_lines and not self.regenerate_cancel_invoice:
                raise UserError(_("You can not create invoice selected date range"))
            advance_lines = lines.filtered(
                lambda sl: (sl.so_line_id.order_id.clx_invoice_policy_id.policy_type == 'advance'))
            if self.regenerate_cancel_invoice:
                advance_lines = advance_lines.filtered(
                    lambda x: x.cancel_invoice_start_date and x.cancel_invoice_end_date)
            partner_id.with_context(generate_invoice_date_range=True, start_date=self.start_date,
                                    end_date=self.end_date,
                                    regenerate_invoice=self.regenerate_cancel_invoice).generate_advance_invoice(
                advance_lines)
