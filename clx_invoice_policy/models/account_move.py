# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models, api, _
from dateutil import parser

class AccountMove(models.Model):
    _inherit = 'account.move'

    mgmt_company = fields.Many2one(related="partner_id.management_company_type_id", store=True)
    subscription_line_ids = fields.One2many('sale.subscription.line', 'account_id', string="Subscription Lines")
    invoices_month_year = fields.Char(string="Invoicing Period", compute="set_invoices_month", store=False)

    def set_invoices_month(self):
        start_date = False
        for record in self:
            if record.invoice_line_ids:
                for line in record.invoice_line_ids:
                    if "Invoicing period" in line.name:
                        name = line.name.split(':')[-1]
                        name = name.split('-')
                        start_date = parser.parse(name[0])
                        end_date = parser.parse(name[-1])
                if start_date:
                    record.invoices_month_year = start_date.strftime("%b, %Y")
                else:
                    record.invoices_month_year = " "

    def _get_sequence(self):
        res = super(AccountMove, self)._get_sequence()
        sequence = self.env.ref("clx_invoice_policy.sequence_greystar_sequence")
        if self.partner_id.management_company_type_id and self.partner_id.management_company_type_id.name:
            management_partner = self.env['res.partner'].search(
                [('id', '=', self.partner_id.management_company_type_id.id),
                 ('name', 'ilike', 'Greystar')])
            if management_partner and sequence:
                return sequence
        return res

    def button_cancel(self):
        res = super(AccountMove, self).button_cancel()
        if self.invoice_origin:
            sale_order = self.env['sale.order'].search([('name', '=', self.invoice_origin)])
            if sale_order and not sale_order.is_ratio:
                order_lines_list = sale_order.order_line.ids
                subscription_lines = self.env['sale.subscription.line'].search([('so_line_id', 'in', order_lines_list)])
                subscriptions = subscription_lines.mapped('analytic_account_id')
                subscription_lines = subscriptions.recurring_invoice_line_ids
                for line in self.invoice_line_ids:
                    sub_lines = subscription_lines.filtered(lambda x: x.product_id.categ_id.id == line.category_id.id)
                    dates_list = line.name.split(':')[-1].split('-')
                    start_date = parser.parse(dates_list[0])
                    end_date = parser.parse(dates_list[-1])
                    for sub_line in sub_lines:
                        sub_line.invoice_start_date = start_date
                        sub_line.invoice_end_date = end_date
        return res


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    category_id = fields.Many2one('product.category', string="Category")
    subscription_ids = fields.Many2many(
        'sale.subscription', string="Subscription(s)")

    management_fees = fields.Float(string="Management Fees")
    retail_price = fields.Float(string="Retails Price")
    wholesale = fields.Float(string="Wholsesale")
