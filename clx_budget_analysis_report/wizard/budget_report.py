# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, models
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
from datetime import timedelta
from calendar import monthrange
import datetime


class BudgetReportWizard(models.TransientModel):
    _name = 'budget.report.wizard'

    partner_ids = fields.Many2many('res.partner', string="Customers")
    start_date = fields.Date(string="Start Date", default=datetime.datetime(fields.Date.today().year, 1, 1).date())
    end_date = fields.Date(string="End Date")

    def _calculate_wholesale_price(self, subscription_line, price_unit, price_list):
        wholesale = 0.0
        if subscription_line and price_unit and price_list:
            rule = price_list[0].item_ids.filtered(
                lambda x: x.categ_id.id == subscription_line.product_id.categ_id.id)
            if rule:
                percentage_management_price = custom_management_price = 0.0
                if rule.is_percentage:
                    percentage_management_price = price_unit * (
                            (rule.percent_mgmt_price or 0.0) / 100.0)
                if rule.is_custom and price_unit > rule.min_retail_amount:
                    custom_management_price = price_unit * (
                            (rule.percent_mgmt_price or 0.0) / 100.0)
                management_fees = max(percentage_management_price,
                                      custom_management_price,
                                      rule.fixed_mgmt_price)
                if rule.is_wholesale_percentage:
                    wholesale = price_unit * (
                            (rule.percent_wholesale_price or 0.0) / 100.0)
                if rule.is_wholesale_formula:
                    wholesale = price_unit - management_fees
        return wholesale

    def get_budget_report(self):
        self._cr.execute("DELETE FROM sale_subscription_report_data")
        report_data_table = self.env['sale.subscription.report.data']
        params = self.env['ir.config_parameter'].sudo()
        budget_month = int(params.get_param('budget_month')) or False
        current_month_start_date = fields.Date.today().replace(day=1)
        yearly_subscription_lines = self.env['sale.subscription.line'].search(
            [('start_date', '!=', False), ('analytic_account_id.partner_id', 'in', self.partner_ids.ids),
             ('product_id.subscription_template_id.recurring_rule_type', '=', 'yearly')])
        # yearly_subscription_lines = yearly_subscription_lines.filtered(
        #     lambda x: x.start_date >= current_month_start_date)
        if yearly_subscription_lines:
            for sub in yearly_subscription_lines:
                if sub.end_date:
                    r = len(OrderedDict(((sub.start_date + timedelta(_)).strftime("%B-%Y"), 0) for _ in
                                        range((sub.end_date - sub.start_date).days)))
                    if r == 0:
                        budget_month = 1
                    else:
                        budget_month = r
                else:
                    budget_month = 12
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
                    'end_date': end_date_line if not sub.end_date else False
                }
                report_data = report_data_table.create(vals)
                yearly_line_lst = []
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
                    yearly_line_lst.append(vals)
                report_data = report_data_table.create(yearly_line_lst)
        subscription_lines = self.env['sale.subscription.line'].search(
            [('analytic_account_id.partner_id', 'in', self.partner_ids.ids), ('start_date', '!=', False),
             ('product_id.subscription_template_id.recurring_rule_type', '=', 'monthly')], order='start_date asc')
        for subscription_line in subscription_lines:
            if subscription_line.end_date:
                r = len(OrderedDict(((subscription_line.start_date + timedelta(_)).strftime("%B-%Y"), 0) for _ in
                                    range((subscription_line.end_date - subscription_line.start_date).days)))
                if r == 0:
                    budget_month = 1
                else:
                    budget_month = r
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
                    vals.update({'upsell_down_sell_price': subscription_line.price_unit})
                    available_line.write(vals)
                    price_unit = vals['base_price']
                    if price_list and price_unit:
                        wholesale = self._calculate_wholesale_price(subscription_line, price_unit, price_list)
                        available_line.write({'wholesale_price': wholesale if wholesale > 0 else 0})
                else:
                    report_data = report_data_table.create(vals)
                    wholesale = 0.0
                    if report_data:
                        price_unit = vals['base_price']
                        if price_list and price_unit and starting_line:
                            wholesale = self._calculate_wholesale_price(subscription_line, price_unit, price_list)
                        report_data.write({'wholesale_price': wholesale if wholesale > 0 else 0})
                current_month_start_date = current_month_start_date + relativedelta(months=1)
                current_month_start_date = current_month_start_date.replace(day=1)
            budget_month = int(params.get_param('budget_month')) or False
        all_report_data = report_data_table.search([]).filtered(lambda x: x.date > self.end_date)
        if all_report_data:
            all_report_data.unlink()
        all_report_data = report_data_table.search([]).filtered(lambda x: x.date < self.start_date)
        if all_report_data:
            all_report_data.unlink()
        action = self.env.ref(
            'clx_budget_analysis_report.sale_budget_report_action').read()[0]
        return action
