# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from odoo import models
from dateutil import parser
from calendar import monthrange
from collections import OrderedDict


class Partner(models.Model):
    _inherit = 'res.partner'

    def generate_advance_invoice_co_op(self, sub_lines):
        """
        This method is used for the create co-op invoices per sale order lines wise and category wise
        :param sub_lines: recordset of subscriptions lines
        :return: No return
        """
        if sub_lines:
            prepared_lines = [line.with_context({
                'advance': True,
                'partner_id': self._context.get('partner_id', False),
                'percantage': self._context.get('percantage', False),
                'co_op': self._context.get('co_op')
            })._prepare_invoice_line() for line in sub_lines]
            print(prepared_lines)
            for line in prepared_lines:
                if 'line_type' in line:
                    del line['line_type']
            order = sub_lines[0].so_line_id.order_id
            vals = {
                'ref': order.client_order_ref,
                'type': 'out_invoice',
                'invoice_origin': '/'.join(sub_lines.mapped('so_line_id').mapped('order_id').mapped('name')),
                'invoice_user_id': order.user_id.id,
                'narration': order.note,
                'partner_id': self._context.get('partner_id'),
                'fiscal_position_id': order.fiscal_position_id.id or self.property_account_position_id.id,
                'partner_shipping_id': order.partner_shipping_id.id,
                'currency_id': order.pricelist_id.currency_id.id,
                'invoice_payment_ref': order.reference,
                'invoice_payment_term_id': order.payment_term_id.id,
                'invoice_partner_bank_id': order.company_id.partner_id.bank_ids[:1].id,
                'team_id': order.team_id.id,
                'campaign_id': order.campaign_id.id,
                'medium_id': order.medium_id.id,
                'source_id': order.source_id.id,
                'invoice_line_ids': [
                    (0, 0, x) for x in prepared_lines
                ]
            }
            discount_line = self.add_discount_line(vals['invoice_line_ids'])
            if discount_line:
                vals['invoice_line_ids'].append((0, 0, discount_line))
            account_id = self.env['account.move'].create(vals)