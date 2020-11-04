# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.


from odoo import models, fields, api, _
from odoo.exceptions import UserError


class GenerateInvoiceDateRange(models.TransientModel):
    _name = "generate.invoice.date.range"

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')

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
                ('so_line_id.order_id.state', '=', 'sale'),
            ])
            so_lines = lines.filtered(lambda x: x.invoice_start_date and x.invoice_start_date <= self.start_date)
            if not so_lines:
                raise UserError(_("You can not create invoice selected date range"))
            elif so_lines:
                areas_lines = lines.filtered(
                    lambda sl: (sl.so_line_id.order_id.clx_invoice_policy_id.policy_type == 'arrears'))
                advance_lines = lines.filtered(
                    lambda sl: (sl.so_line_id.order_id.clx_invoice_policy_id.policy_type == 'advance'))
                partner_id.with_context(generate_invoice_date_range=True, start_date=self.start_date,
                                        end_date=self.end_date).generate_advance_invoice(advance_lines)
                print(advance_lines, areas_lines)
