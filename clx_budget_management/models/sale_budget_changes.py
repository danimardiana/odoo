# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from dateutil.relativedelta import relativedelta
from odoo import fields, models


class SaleBudgetChanges(models.Model):
    _name = 'sale.budget.changes'
    _description = 'Sale Budget Changes'

    partner_id = fields.Many2one('res.partner', string="Customer")
    product_id = fields.Many2one('product.product', string="Product")
    start_date = fields.Date(sting="Start Date")
    end_date = fields.Date(sting="End Date")
    price = fields.Float(string="Price")
    total_budget = fields.Float(string="Total Budget")
    sol_line_id = fields.Many2one('sale.order.line', string='Sale Order Line')
    line_type = fields.Selection([
        ('base', 'Base'),
        ('upsell', 'Upsell'),
        ('downsell', 'Downsell')
    ], string='Type')

    def _create_sale_budget_changes(self, sale_order):
        price = 0.0
        params = self.env['ir.config_parameter'].sudo()
        budget_month = int(params.get_param('budget_month')) or False
        if sale_order:
            subscription_lines = sale_order.order_line.mapped('subscription_id').recurring_invoice_line_ids
            budget_line = self.search([])
            for line in subscription_lines:
                if line.so_line_id.id not in budget_line.mapped('sol_line_id').ids:
                    total_budget = line.analytic_account_id.recurring_total
                    if line.line_type == 'base':
                        price = line.price_unit
                    elif line.line_type == 'upsell':
                        base_line = line.analytic_account_id.recurring_invoice_line_ids.filtered(
                            lambda x: x.line_type == 'base')
                        if base_line:
                            price = base_line[0].price_unit + line.price_unit
                    elif line.line_type == 'downsell':
                        price = line.price_unit
                    vals = {
                        'partner_id': line.analytic_account_id.partner_id.id,
                        'product_id': line.product_id.id,
                        'start_date': line.start_date,
                        'end_date': line.end_date,
                        'sol_line_id': line.so_line_id.id,
                        'price': price,
                        'line_type': line.line_type,
                        'total_budget': total_budget
                    }
                    self.create(vals)
                    start_date = line.start_date
                    for month_count in range(1, budget_month):
                        total_budget = line.analytic_account_id.recurring_total
                        if line.line_type == 'base':
                            price = line.price_unit
                        elif line.line_type == 'upsell':
                            base_line = line.analytic_account_id.recurring_invoice_line_ids.filtered(
                                lambda x: x.line_type == 'base')
                            if base_line:
                                price = base_line[0].price_unit + line.price_unit
                        elif line.line_type == 'downsell':
                            price = line.price_unit
                        start_date = start_date + relativedelta(months=1)
                        vals = {
                            'partner_id': line.analytic_account_id.partner_id.id,
                            'product_id': line.product_id.id,
                            'start_date': start_date,
                            'end_date': line.end_date,
                            'sol_line_id': line.so_line_id.id,
                            'price': price,
                            'line_type': line.line_type,
                            'total_budget': total_budget
                        }
                        available_line = budget_line.filtered(
                            lambda x: x.partner_id.id == line.analytic_account_id.partner_id.id
                                      and x.product_id.id == line.product_id.id and x.start_date == line.start_date
                            )
                        if available_line:
                            available_line[0].write(vals)
                        if not available_line:
                            self.create(vals)
