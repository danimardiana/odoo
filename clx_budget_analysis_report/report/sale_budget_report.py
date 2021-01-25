# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models, tools, api
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
from datetime import timedelta
from calendar import monthrange


class SaleSubscriptionData(models.Model):
    _name = "sale.subscription.report.data"

    date = fields.Date('Date', readonly=True)
    end_date = fields.Date(string='End Date', readonly=True)
    product_id = fields.Many2one('product.product', readonly=True)
    subscription_id = fields.Many2one('sale.subscription', readonly=True)
    subscription_line_id = fields.Many2one('sale.subscription.line', readonly=True)
    partner_id = fields.Many2one('res.partner', string="Customer", readonly=True)
    wholesale_price = fields.Float(string='Wholesale Price', readonly=True)
    price = fields.Float(string='Price', readonly=True)
    base_price = fields.Float(string="Price")
    upsell_down_sell_price = fields.Float(string="Upsell Downsell Price", default=0.0)


class SaleBudgetReport(models.Model):
    """ Sale Budget report """

    _name = "sale.budget.report"
    _auto = False
    _description = "Sale Budget Report"
    _rec_name = "id"

    @api.model
    def fields_view_get(self, view_id=None, view_type='pivot', toolbar=False, submenu=False):
        res = super(SaleBudgetReport, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=False)
        if view_type == 'pivot':
            self.init()
        return res

    date = fields.Date('Date', readonly=True)
    end_date = fields.Date(string='End Date', readonly=True)
    product_id = fields.Many2one('product.product', readonly=True)
    subscription_id = fields.Many2one('sale.subscription', readonly=True)
    subscription_line_id = fields.Many2one('sale.subscription.line', readonly=True)
    partner_id = fields.Many2one('res.partner', string="Customer", readonly=True)
    wholesale_price = fields.Float(string='Wholesale Price')
    price = fields.Float(string='Price')
    base_price = fields.Float(readonly=True)
    upsell_down_sell_price = fields.Float(readonly=True)

    def _query(self):
        return """SELECT sbl.id,sbl.date as date,
         sbl.product_id as product_id,
         sbl.subscription_id as subscription_id,
         sbl.subscription_line_id as subscription_line_id,
         sbl.partner_id as partner_id,
         sbl.wholesale_price as wholesale_price,
         sbl.base_price as price,
         sbl.end_date as end_date
        from sale_subscription_report_data AS sbl group by sbl.partner_id,sbl.id"""

    def init(self):
        report_data_table = self.env['sale.subscription.report.data']
        report_data_table.search([]).unlink()
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
                    # base = sub.analytic_account_id.recurring_invoice_line_ids.filtered(lambda x: x.line_type == 'base'
                    #                                                                              and x.product_id.id == sub.product_id.id)

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
            # elif subscription_line.line_type == 'upsell' and subscription_line.end_date:
            current_month_start_date = subscription_line.start_date
            for i in range(0, budget_month):
                base = subscription_line.analytic_account_id.recurring_invoice_line_ids.filtered(lambda
                                                                                                     x: x.line_type == 'base'
                                                                                                        and x.product_id.id == subscription_line.product_id.id)
                end_date_line = current_month_start_date.replace(
                    day=monthrange(current_month_start_date.year, current_month_start_date.month)[1])
                end_date_x = subscription_line.end_date if subscription_line.end_date and subscription_line.end_date <= end_date_line else end_date_line
                base_price = base[0].price_unit / 2 if (current_month_start_date.day > 15) or (end_date_x.day < 15) else \
                    base[0].price_unit
                starting_line = subscription_line.analytic_account_id.recurring_invoice_line_ids.filtered(
                    lambda x: x.start_date <= subscription_line.start_date)
                for sub_line in starting_line:
                    if sub_line.end_date and subscription_line.start_date >= sub_line.end_date:
                        starting_line -= sub_line
                print("TTTTTTTTTTTTTTTTTTTTTTTtt", starting_line)
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
                    # 'wholesale_price': subscription_line.so_line_id.wholesale_price,
                    'base_price': s_sum,
                    'end_date': subscription_line.end_date if subscription_line.end_date and subscription_line.end_date <= end_date_line else end_date_line
                }
                price_list = subscription_line.so_line_id.order_id.pricelist_id
                if subscription_line.line_type in ('upsell', 'downsell'):
                    wholesale = subscription_line.so_line_id.wholesale_price
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
                    if starting_line:
                        s_sum = 0.0
                        for s_line in starting_line:
                            if current_month_start_date.day > 15 or end_date_x.day < 15:
                                s_sum += s_line.price_unit / 2
                            else:
                                s_sum += s_line.price_unit
                        price_unit = s_sum
                    if price_list and price_unit:
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
                        available_line.write({'wholesale_price': wholesale if wholesale > 0 else 0})
                # if not all_report_data:
                #     report_data_table.create(vals)
                else:
                    report_data = report_data_table.create(vals)
                    wholesale = 0.0
                    if report_data:
                        price_unit = 0.0
                        starting_line = subscription_line.analytic_account_id.recurring_invoice_line_ids.filtered(
                            lambda x: x.start_date <= subscription_line.start_date)

                        if starting_line:
                            s_sum = 0.0
                            for s_line in starting_line:
                                if current_month_start_date.day > 15 or end_date_x.day < 15:
                                    s_sum += s_line.price_unit / 2
                                else:
                                    s_sum += s_line.price_unit
                            price_unit = s_sum
                        if price_list and price_unit and starting_line:
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
                        report_data.write({'wholesale_price': wholesale if wholesale > 0 else 0})
                current_month_start_date = current_month_start_date + relativedelta(months=1)
                current_month_start_date = current_month_start_date.replace(day=1)
            budget_month = int(params.get_param('budget_month')) or False
            current_month_start_date = fields.Date.today().replace(day=1)

        # if subscription start date is behind current date and end date is not set on subscription than
        # report will be generate current month to budget month
        # subscription_lines = all_subscription_lines.filtered(
        #     lambda x: not x.end_date and x.start_date < current_month_start_date)
        # for subscription_line in subscription_lines:
        #     if subscription_line.analytic_account_id.code == 'SUB348':
        #         print("___________")
        #     if subscription_line.line_type == 'upsell':
        #         current_month_start_date = subscription_line.start_date
        #         budget_month = int(params.get_param('budget_month')) or False
        #         budget_month -= subscription_line.start_date.month - starting_month.month
        #
        #     for i in range(0, budget_month):
        #         end_date_line = current_month_start_date.replace(
        #             day=monthrange(current_month_start_date.year, current_month_start_date.month)[1])
        #         vals = {
        #             'date': current_month_start_date,
        #             'product_id': subscription_line.product_id.id,
        #             'subscription_id': subscription_line.analytic_account_id.id,
        #             'subscription_line_id': subscription_line.id,
        #             'partner_id': subscription_line.so_line_id.order_id.partner_id.id,
        #             'wholesale_price': subscription_line.so_line_id.wholesale_price,
        #             'base_price': subscription_line.analytic_account_id.recurring_invoice_line_ids.filtered(
        #                 lambda x: x.line_type == 'base')[0].price_unit,
        #             'end_date': end_date_line
        #         }
        #         if subscription_line.line_type in ('upsell', 'downsell'):
        #             wholesale = subscription_line.so_line_id.wholesale_price
        #             price_unit = subscription_line.price_unit + base[
        #                 0].price_unit
        #             price_list = subscription_line.so_line_id.order_id.pricelist_id
        #             if price_list:
        #                 rule = price_list[0].item_ids.filtered(
        #                     lambda x: x.categ_id.id == subscription_line.product_id.categ_id.id)
        #                 if rule:
        #                     percentage_management_price = custom_management_price = 0.0
        #                     if rule.is_percentage:
        #                         percentage_management_price = price_unit * (
        #                                 (rule.percent_mgmt_price or 0.0) / 100.0)
        #                     if rule.is_custom and price_unit > rule.min_retail_amount:
        #                         custom_management_price = price_unit * (
        #                                 (rule.percent_mgmt_price or 0.0) / 100.0)
        #                     management_fees = max(percentage_management_price,
        #                                           custom_management_price,
        #                                           rule.fixed_mgmt_price)
        #                     if rule.is_wholesale_percentage:
        #                         wholesale = price_unit * (
        #                                 (rule.percent_wholesale_price or 0.0) / 100.0)
        #                     if rule.is_wholesale_formula:
        #                         wholesale = price_unit - management_fees
        #             vals.update({
        #                 'upsell_down_sell_price': subscription_line.price_unit,
        #                 'wholesale_price': wholesale
        #             })
        #         available_line = report_data_table.search([('date', '=', current_month_start_date),
        #                                                    ('product_id', '=', subscription_line.product_id.id),
        #                                                    ('subscription_id', '=',
        #                                                     subscription_line.analytic_account_id.id),
        #                                                    ('partner_id', '=',
        #                                                     subscription_line.so_line_id.order_id.partner_id.id)
        #                                                    ])
        #
        #         if not available_line:
        #             report_data_table.create(vals)
        #         current_month_start_date = current_month_start_date + relativedelta(months=1)
        #     budget_month = int(params.get_param('budget_month')) or False
        #     current_month_start_date = fields.Date.today().replace(day=1)

        all_report_data = report_data_table.search([]).filtered(lambda x: x.date > end_date)
        if all_report_data:
            all_report_data.unlink()
        all_report_data = report_data_table.search([]).filtered(lambda x: x.date < current_month_start_date)
        if all_report_data:
            all_report_data.unlink()
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
            )
        """ % (self._table, self._query()))
