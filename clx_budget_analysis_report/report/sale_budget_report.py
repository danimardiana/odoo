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
    product_id = fields.Many2one('product.product', readonly=True)
    subscription_id = fields.Many2one('sale.subscription', readonly=True)
    subscription_line_id = fields.Many2one('sale.subscription.line', readonly=True)
    partner_id = fields.Many2one('res.partner', readonly=True)
    wholesale_price = fields.Float(string='Wholesale Price', readonly=True)
    price = fields.Float(string='Price', readonly=True)
    base_price = fields.Float(string="Price")
    upsell_down_sell_price = fields.Float(string="Price", default=0.0)


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
    product_id = fields.Many2one('product.product', readonly=True)
    subscription_id = fields.Many2one('sale.subscription', readonly=True)
    subscription_line_id = fields.Many2one('sale.subscription.line', readonly=True)
    partner_id = fields.Many2one('res.partner', readonly=True)
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
         sbl.base_price + sbl.upsell_down_sell_price as price
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
                if sub.analytic_account_id.code == 'SUB556':
                    print("----------------")
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
                vals = {
                    'date': sub.start_date,
                    'product_id': sub.product_id.id,
                    'subscription_id': sub.analytic_account_id.id,
                    'subscription_line_id': sub.id,
                    'partner_id': sub.so_line_id.order_id.partner_id.id,
                    'wholesale_price': sub.so_line_id.wholesale_price,
                    'base_price': base[0].price_unit,
                }
                report_data = report_data_table.create(vals)
                for i in range(0, budget_month - 1):
                    # base = sub.analytic_account_id.recurring_invoice_line_ids.filtered(lambda x: x.line_type == 'base'
                    #                                                                              and x.product_id.id == sub.product_id.id)

                    vals = {
                        'date': current_month_start_date,
                        'product_id': sub.product_id.id,
                        'subscription_id': sub.analytic_account_id.id,
                        'subscription_line_id': sub.id,
                        'partner_id': sub.so_line_id.order_id.partner_id.id,
                        'wholesale_price': sub.so_line_id.wholesale_price,
                        'base_price': 0.0,
                    }
                    report_data = report_data_table.create(vals)

        all_subscription_lines = self.env['sale.subscription.line'].search(
            [('start_date', '!=', False), ('product_id.subscription_template_id.recurring_rule_type', '=', 'monthly')])
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
                vals = {
                    'date': current_month_start_date,
                    'product_id': subscription_line.product_id.id,
                    'subscription_id': subscription_line.analytic_account_id.id,
                    'subscription_line_id': subscription_line.id,
                    'partner_id': subscription_line.so_line_id.order_id.partner_id.id,
                    'wholesale_price': subscription_line.so_line_id.wholesale_price,
                    'base_price': base[0].price_unit,
                }
                r = end_date_line - current_month_start_date
                if r.days + 1 in (30, 31, 28):
                    print("_______")
                elif r.days < 30 or r.days < 31:
                    per_day_price = base[0].price_unit / end_date_line.day
                    new_price = per_day_price * r.days
                    # calculation for the wholesale price in days
                    per_day_wholesale_price = subscription_line.so_line_id.wholesale_price / end_date_line.day
                    new_wholesale_price = per_day_wholesale_price * r.days
                    vals.update({
                        'wholesale_price': new_wholesale_price,
                        'base_price': new_price
                    })
                if subscription_line.line_type == 'upsell':
                    vals.update({
                        'upsell_down_sell_price': subscription_line.price_unit,
                    })
                    base_line = subscription_line.analytic_account_id.recurring_invoice_line_ids.filtered(
                        lambda x: x.line_type == 'base' and x.product_id.id == subscription_line.product_id.id)
                    all_report_data = report_data_table.search([]).filtered(
                        lambda x: x.date.month == current_month_start_date.month
                                  and base_line[0].id == x.subscription_line_id.id
                    )
                    if all_report_data and all_report_data.subscription_line_id.line_type == subscription_line.line_type:
                        all_report_data.update({
                            'upsell_down_sell_price': subscription_line.price_unit,
                        })
                    if not all_report_data:
                        report_data_table.create(vals)
                else:
                    report_data = report_data_table.create(vals)
                current_month_start_date = current_month_start_date + relativedelta(months=1)
                current_month_start_date = current_month_start_date.replace(day=1)
            budget_month = int(params.get_param('budget_month')) or False
            current_month_start_date = fields.Date.today().replace(day=1)

        # if subscription start date is behind current date and end date is not set on subscription than
        # report will be generate current month to budget month
        # subscription_lines = all_subscription_lines.filtered(
        #     lambda x: not x.end_date and x.start_date < current_month_start_date)
        # for subscription_line in subscription_lines:
        #     if subscription_line.analytic_account_id.code == 'SUB412':
        #         print("___________")
        #     if subscription_line.line_type == 'upsell':
        #         current_month_start_date = subscription_line.start_date
        #         budget_month = int(params.get_param('budget_month')) or False
        #         budget_month -= subscription_line.start_date.month - starting_month.month
        #
        #     for i in range(0, budget_month):
        #         vals = {
        #             'date': current_month_start_date,
        #             'product_id': subscription_line.product_id.id,
        #             'subscription_id': subscription_line.analytic_account_id.id,
        #             'subscription_line_id' : subscription_line.id,
        #             'partner_id': subscription_line.so_line_id.order_id.partner_id.id,
        #             'wholesale_price': subscription_line.so_line_id.wholesale_price,
        #             'base_price': subscription_line.analytic_account_id.recurring_invoice_line_ids.filtered(
        #                 lambda x: x.line_type == 'base')[0].price_unit,
        #         }
        #         if subscription_line.line_type == 'upsell':
        #             vals.update({
        #                 'upsell_down_sell_price': subscription_line.price_unit
        #             })
        #         report_data_table.create(vals)
        #         current_month_start_date = current_month_start_date + relativedelta(months=1)
        #     budget_month = int(params.get_param('budget_month')) or False
        #     current_month_start_date = fields.Date.today().replace(day=1)

        all_report_data = report_data_table.search([]).filtered(lambda x: x.date > end_date)
        if all_report_data:
            all_report_data.unlink()
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
            )
        """ % (self._table, self._query()))
