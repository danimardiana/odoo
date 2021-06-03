# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models, api, _
from dateutil import parser
from collections import OrderedDict
from datetime import timedelta


class AccountMove(models.Model):
    _inherit = 'account.move'

    mgmt_company = fields.Many2one(related="partner_id.management_company_type_id", store=True)
    subscription_line_ids = fields.Many2many('sale.subscription.line', 'account_id', string="Subscription Lines")
    invoices_month_year = fields.Char(string="Invoicing Period", compute="set_invoices_month", store=False)
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('approved_draft', 'Approved Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled')
    ], string='Status', required=True, readonly=True, copy=False, tracking=True,
        default='draft')
    def post(self):
        res = super(AccountMove, self).post()
        sequence = self.env.ref("clx_invoice_policy.sequence_greystar_sequence")
        if res and self.partner_id and self.partner_id.management_company_type_id and 'Greystar' in self.partner_id.management_company_type_id.name and sequence:
            self.name = sequence.next_by_code('greystar.sequence')
        return res

    def set_invoices_month(self):
        start_date = False
        for record in self:
            if record.invoice_line_ids:
                for line in record.invoice_line_ids:
                    if "Invoicing period" in line.name:
                        name = line.name.split(':')[-1]
                        name = name.split('-')
                        start_date = parser.parse(name[0])
                if start_date:
                    record.invoices_month_year = start_date.strftime("%b, %Y")
                else:
                    record.invoices_month_year = " "

    def unlink(self):
        for record in self:
            if record.invoice_origin:
                for inv_line in record.invoice_line_ids:
                    if inv_line.subscription_lines_ids:
                        name = inv_line.name.split(':')
                        name = name[-1].split('-')
                        start_date = parser.parse(name[0])
                        end_date = parser.parse(name[-1])
                        if start_date and end_date:
                            for sub in inv_line.subscription_lines_ids:
                                if not sub.end_date:
                                    sub.invoice_start_date = start_date.date()
                                    sub.invoice_end_date = end_date.date()
                                elif sub.end_date:
                                    month_count = len(
                                        OrderedDict(((sub.end_date + timedelta(_)).strftime("%B-%Y"), 0) for _ in
                                                    range((start_date.date() - sub.end_date).days)))
                                    if month_count == 1 and start_date.date() > sub.end_date:
                                        sub.invoice_start_date = sub.start_date
                                        sub.invoice_end_date = sub.end_date
                                    elif sub.start_date > start_date.date():
                                        sub.invoice_start_date = sub.start_date
                                        sub.invoice_end_date = sub.end_date
                                    else:
                                        sub.invoice_start_date = start_date.date()
                                        sub.invoice_end_date = end_date.date()
        return super(AccountMove, self).unlink()

    def button_cancel(self):
        res = super(AccountMove, self).button_cancel()
        if self.invoice_origin:
            for inv_line in self.invoice_line_ids:
                if inv_line.subscription_lines_ids:
                    name = inv_line.name.split(':')
                    name = name[-1].split('-')
                    start_date = parser.parse(name[0])
                    end_date = parser.parse(name[-1])
                    if start_date and end_date:
                        for sub in inv_line.subscription_lines_ids:
                            if not sub.end_date:
                                sub.invoice_start_date = start_date.date()
                                sub.invoice_end_date = end_date.date()
                            elif sub.end_date:
                                month_count = len(
                                    OrderedDict(((sub.end_date + timedelta(_)).strftime("%B-%Y"), 0) for _ in
                                                range((start_date.date() - sub.end_date).days)))
                                if month_count == 1 and start_date.date() > sub.end_date:
                                    sub.invoice_start_date = sub.start_date
                                    sub.invoice_end_date = sub.end_date
                                elif sub.start_date > start_date.date():
                                    sub.invoice_start_date = sub.start_date
                                    sub.invoice_end_date = sub.end_date
                                else:
                                    sub.invoice_start_date = start_date.date()
                                    sub.invoice_end_date = end_date.date()
        return res

    def button_approve_invoice(self):
        for rec in self.filtered(lambda x: x.state == 'draft'):
            rec.state = 'approved_draft'


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    category_id = fields.Many2one('product.category', string="Category")
    subscription_ids = fields.Many2many(
        'sale.subscription', string="Subscription(s)")
    subscription_lines_ids = fields.Many2many('sale.subscription.line', string="Subscriptions Lines")

    management_fees = fields.Float(string="Management Fees")
    retail_price = fields.Float(string="Retails Price")
    wholesale = fields.Float(string="Wholsesale")
    description = fields.Char(string="Description")
