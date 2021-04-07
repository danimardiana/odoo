# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, models, tools, api
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
from datetime import timedelta
from calendar import monthrange


class SaleSubscriptionLine(models.Model):
    _inherit = "sale.subscription.line"

    def budget_pivot_report(self):
        report_data_table = self.env['sale.subscription.report.data']
        # report_data_table.search([]).unlink()
        params = self.env['ir.config_parameter'].sudo()
        budget_month = int(params.get_param('budget_month')) or False
        current_month_start_date = fields.Date.today().replace(day=1)
        starting_month = current_month_start_date
        end_date = current_month_start_date + relativedelta(months=budget_month)
        yearly_subscription_lines = self.env['sale.subscription.line'].search(
            [('start_date', '!=', False), ('product_id.subscription_template_id.recurring_rule_type', '=', 'yearly')])
        yearly_subscription_lines = yearly_subscription_lines.filtered(
            lambda x: x.start_date >= current_month_start_date)
        if yearly_subscription_lines:
            for sub in yearly_subscription_lines:
                if sub.end_date:
                    r = len(OrderedDict(((sub.start_date + timedelta(_)).strftime("%B-%Y"), 0) for _ in
                                        range((sub.end_date - sub.start_date).days)))
                    if r == 0:
                        budget_month = 1
                    else:
                        budget_month = r
                if sub.line_type == 'upsell' and not sub.end_date:
                    current_month_start_date = sub.start_date
                    budget_month = int(params.get_param('budget_month')) or False
                    budget_month -= sub.start_date.month - starting_month.month
                base = sub.analytic_account_id.recurring_invoice_line_ids.filtered(lambda x: x.line_type == 'base'
                                                                                             and x.product_id.id == sub.product_id.id)
                current_month_start_date = sub.start_date
                end_date_line = current_month_start_date.replace(
                    day=monthrange(current_month_start_date.year, current_month_start_date.month)[1])
                vals = {
                    'date': current_month_start_date,
                    'product_id': sub.product_id.id,
                    'subscription_id': sub.analytic_account_id.id,
                    'subscription_line_id': sub.id,
                    'partner_id': sub.so_line_id.order_id.partner_id.id,
                    'wholesale_price': sub.so_line_id.wholesale_price,
                    'base_price': base[0].price_unit,
                    'end_date': end_date_line if not sub.end_date else end_date
                }
                report_data = report_data_table.create(vals)
                for i in range(0, budget_month - 1):
                    current_month_start_date = current_month_start_date + relativedelta(months=1)
                    end_date_line = current_month_start_date.replace(
                        day=monthrange(current_month_start_date.year, current_month_start_date.month)[1])
                    vals = {
                        'date': current_month_start_date,
                        'product_id': sub.product_id.id,
                        'subscription_id': sub.analytic_account_id.id,
                        'subscription_line_id': sub.id,
                        'partner_id': sub.so_line_id.order_id.partner_id.id,
                        'wholesale_price': sub.so_line_id.wholesale_price,
                        'base_price': sub.price_unit,
                        'end_date': end_date_line if not sub.end_date else sub.end_date
                    }
                    report_data = report_data_table.create(vals)
                current_month_start_date = fields.Date.today().replace(day=1)
        current_month_start_date = fields.Date.today().replace(day=1)
        all_subscription_lines = self.env['sale.subscription.line'].search(
            [('start_date', '!=', False),
             ('product_id.subscription_template_id.recurring_rule_type', '=', 'monthly')])
        subscription_lines = all_subscription_lines.filtered(lambda x: x.start_date >= current_month_start_date)
        for subscription_line in subscription_lines:
            if subscription_line.end_date:
                r = len(OrderedDict(((subscription_line.start_date + timedelta(_)).strftime("%B-%Y"), 0) for _ in
                                    range((subscription_line.end_date - subscription_line.start_date).days)))
                if r == 0:
                    budget_month = 1
                else:
                    budget_month = r
            if subscription_line.line_type == 'upsell' and not subscription_line.end_date:
                current_month_start_date = subscription_line.start_date
                budget_month = int(params.get_param('budget_month')) or False
                budget_month -= subscription_line.start_date.month - starting_month.month
            current_month_start_date = subscription_line.start_date
            for i in range(0, budget_month):
                end_date_line = current_month_start_date.replace(
                    day=monthrange(current_month_start_date.year, current_month_start_date.month)[1])
                end_date_x = subscription_line.end_date if subscription_line.end_date and subscription_line.end_date <= end_date_line else end_date_line
                starting_line = subscription_line.analytic_account_id.recurring_invoice_line_ids.filtered(
                    lambda x: x.start_date <= subscription_line.start_date)
                for sub_line in starting_line:
                    if sub_line.end_date and subscription_line.start_date >= sub_line.end_date:
                        starting_line -= sub_line
                s_sum = 0.0
                for s_line in starting_line:
                    if current_month_start_date.day > 15 or end_date_x.day < 15:
                        s_sum += s_line.price_unit / 2
                    else:
                        s_sum += s_line.price_unit
                vals = {
                    'date': current_month_start_date,
                    'product_id': subscription_line.product_id.id,
                    'subscription_id': subscription_line.analytic_account_id.id,
                    'subscription_line_id': subscription_line.id,
                    'partner_id': subscription_line.so_line_id.order_id.partner_id.id,
                    'base_price': s_sum,
                    'end_date': subscription_line.end_date if subscription_line.end_date and subscription_line.end_date <= end_date_line else end_date_line
                }
                price_list = subscription_line.so_line_id.order_id.pricelist_id
                if subscription_line.line_type in ('upsell', 'downsell'):
                    vals.update({
                        'upsell_down_sell_price': subscription_line.price_unit,
                    })
                available_line = report_data_table.search([('date', '=', current_month_start_date),
                                                           ('product_id', '=', subscription_line.product_id.id),
                                                           ('subscription_id', '=',
                                                            subscription_line.analytic_account_id.id),
                                                           ('partner_id', '=',
                                                            subscription_line.so_line_id.order_id.partner_id.id)
                                                           ], limit=1)
                if available_line:
                    price_unit = 0.0
                    vals.update({'upsell_down_sell_price': subscription_line.price_unit})
                    available_line.write(vals)
                    starting_line = subscription_line.analytic_account_id.recurring_invoice_line_ids.filtered(
                        lambda x: x.start_date <= subscription_line.start_date)
                    for sub_line in starting_line:
                        if sub_line.end_date and subscription_line.start_date >= sub_line.end_date:
                            starting_line -= sub_line
                    if starting_line:
                        s_sum = 0.0
                        for s_line in starting_line:
                            if current_month_start_date.day > 15 or end_date_x.day < 15:
                                s_sum += s_line.price_unit / 2
                            else:
                                s_sum += s_line.price_unit
                        price_unit = s_sum
                    if price_list and price_unit:
                        wholesale = self._calculate_wholesale_price(subscription_line, price_unit, price_list)
                        available_line.write({'wholesale_price': wholesale if wholesale > 0 else 0})
                else:
                    report_data = report_data_table.create(vals)
                    wholesale = 0.0
                    price_unit = 0.0
                    if report_data:
                        starting_line = subscription_line.analytic_account_id.recurring_invoice_line_ids.filtered(
                            lambda x: x.start_date <= subscription_line.start_date)
                        for sub_line in starting_line:
                            if sub_line.end_date and subscription_line.start_date >= sub_line.end_date:
                                starting_line -= sub_line
                        if starting_line:
                            s_sum = 0.0
                            for s_line in starting_line:
                                if current_month_start_date.day > 15 or end_date_x.day < 15:
                                    s_sum += s_line.price_unit / 2
                                else:
                                    s_sum += s_line.price_unit
                            price_unit = s_sum
                        if price_list and price_unit and starting_line:
                            wholesale = self._calculate_wholesale_price(subscription_line, price_unit, price_list)
                        report_data.write({'wholesale_price': wholesale if wholesale > 0 else 0})
                current_month_start_date = current_month_start_date + relativedelta(months=1)
                current_month_start_date = current_month_start_date.replace(day=1)
            budget_month = int(params.get_param('budget_month')) or False
            current_month_start_date = fields.Date.today().replace(day=1)
        all_report_data = report_data_table.search([]).filtered(lambda x: x.date > end_date)
        if all_report_data:
            all_report_data.unlink()
        all_report_data = report_data_table.search([]).filtered(lambda x: x.date < current_month_start_date)
        if all_report_data:
            all_report_data.unlink()
