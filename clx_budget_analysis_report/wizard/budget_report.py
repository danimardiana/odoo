# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, models, api
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
from datetime import timedelta
from calendar import monthrange, month_name
import datetime
import json


class BudgetReportWizard(models.TransientModel):
    _name = 'budget.report.wizard'
    _description = "Budget Report Wizard"

    partner_ids = fields.Many2many('res.partner', string="Customers")
    start_date = fields.Date(string="Start Date", default=datetime.datetime(
        fields.Date.today().year, 1, 1).date())
    end_date = fields.Date(string="End Date")

    def reset(self):
        self.partner_ids = False
        action = self.env.ref(
            'clx_budget_analysis_report.action_budget_report_wizard').read()[0]
        return action

    @api.model
    def default_get(self, fields):
        result = super(BudgetReportWizard, self).default_get(fields)
        wizard_records = self.search([], order='id DESC')
        if wizard_records:
            result.update({'partner_ids': wizard_records[0].partner_ids.ids,
                           'start_date': wizard_records[0].start_date,
                           'end_date': wizard_records[0].end_date
                           })
        return result

    def get_budget_report(self):
        self._cr.execute("DELETE FROM sale_subscription_report_data")
        report_data_table = self.env['sale.subscription.report.data']
        params = self.env['ir.config_parameter'].sudo()
        # search all subscriptions lines for the client
        subscription_lines = self.env['sale.subscription.line'].search(
            [('analytic_account_id.partner_id', 'in', self.partner_ids.ids),
             ('start_date', '!=', False),
             # ('product_id.subscription_template_id.recurring_rule_type', '=', 'monthly'),
             '|', ('end_date', '>=', self.start_date), ('end_date', '=', False),
             ('start_date', '<=', self.end_date),
             ],
            order='start_date asc')
        if not len(subscription_lines):
            return
        slider_start_date = self.start_date.replace(day=1)
        slider_end_date = self.start_date.replace(day=monthrange(
            slider_start_date.year, slider_start_date.month)[1])
        slider_period = month_name[slider_start_date.month] + \
            ' ' + str(slider_start_date.year)
        result_table = {}
        price_list = {}
        price_list_processed = []
        while True:
            result_table[slider_period] = {}
            for sub_line in subscription_lines:
                # check if our sub_line intersect with period
                retail_price = self.env['sale.subscription.line'].get_subscription_line_retail_period(
                    sub_line, slider_start_date, slider_end_date)
                # just pass sub.line if no spending this month
                if not retail_price:
                    continue
                price_list_id = sub_line.so_line_id.order_id.pricelist_id
                # pricelist needed to calculate wholesale only
                if not price_list_id in price_list_processed:
                    price_list.update(self.env['sale.subscription'].pricelist_flatten(
                        price_list_id))
                    price_list_processed.append(
                        price_list_id)

                product_stamp = str(
                    sub_line.so_line_id.order_id.partner_id.id)+'_'+str(sub_line.product_id.id)
                if (product_stamp in result_table[slider_period]):
                    result_table[slider_period][product_stamp]['retail_price'] += retail_price
                else:
                    tags = [str(price_list_id.id) + '_0_' + str(sub_line.product_id.id),
                            str(price_list_id.id) + '_1_' +
                            str(sub_line.product_id.product_tmpl_id.id),
                            str(price_list_id.id) + '_2_' +
                            str(sub_line.product_id.categ_id.id),
                            str(price_list_id.id) + '_3',
                            list(price_list.keys())[0]]
                    for tag in tags:
                        if tag in price_list:
                            pricelist2process = price_list[tag]
                            break
                    result_start_date = slider_start_date if slider_start_date >= sub_line.start_date else sub_line.start_date
                    result_end_date = slider_start_date.replace(day=monthrange(
                        slider_start_date.year, slider_start_date.month)[1])
                    if sub_line.end_date and sub_line.end_date < result_end_date:
                        result_end_date = sub_line.end_date 
                    result_table[slider_period][product_stamp] = {
                        'period': slider_period,
                        'start_date': result_start_date,
                        'product_id': sub_line.product_id.id,
                        'subscription_id': sub_line.analytic_account_id.id,
                        'subscription_line_id': sub_line.id,
                        'partner_id': sub_line.so_line_id.order_id.partner_id.id,
                        # will be calculated based on final amount later
                        'wholesale_price': pricelist2process,
                        'end_date': result_end_date,
                        'retail_price': retail_price,
                        'description': sub_line.so_line_id.name,
                        'category': sub_line.product_id.categ_id.id,
                        'company_name': sub_line.so_line_id.order_id.partner_id.name
                    }

            slider_start_date += relativedelta(months=1)
            slider_end_date = slider_start_date.replace(day=monthrange(
                slider_start_date.year, slider_start_date.month)[1])
            slider_period = month_name[slider_start_date.month] + \
                ' ' + str(slider_start_date.year)
            if (slider_end_date > self.end_date):
                break
        # saving to the report table
        for period in result_table.keys():
            for subscription in result_table[period].keys():
                sale_line_write = result_table[period][subscription]
                result_table[period][subscription].update(self.env['sale.subscription'].subscription_wholesale_period(
                    sale_line_write['retail_price'], sale_line_write['wholesale_price']))
                report_data_table.create(sale_line_write)

        # action = self.env.ref(
        #     'clx_budget_analysis_report.'+self.env.context['action_next']).read()[0]

        action = self.env.ref(
            'clx_budget_analysis_report.'+self.env.context['action_next']).read()[0]

        return action

    def get_budget_report_old(self):
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
                    current_month_start_date = current_month_start_date + \
                        relativedelta(months=1)
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
                    elif sub_line.end_date and sub_line.end_date < end_date_x:
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
                                                           ('product_id', '=',
                                                            subscription_line.product_id.id),
                                                           ('subscription_id', '=',
                                                            subscription_line.analytic_account_id.id),
                                                           ('partner_id', '=',
                                                            subscription_line.so_line_id.order_id.partner_id.id)
                                                           ], limit=1)
                if available_line:
                    vals.update(
                        {'upsell_down_sell_price': subscription_line.price_unit})
                    available_line.write(vals)
                    price_unit = vals['base_price']
                    if price_list and price_unit:
                        wholesale = self._calculate_wholesale_price(
                            subscription_line, price_unit, price_list)
                        available_line.write(
                            {'wholesale_price': wholesale if wholesale > 0 else 0})
                else:
                    report_data = report_data_table.create(vals)
                    wholesale = 0.0
                    if report_data:
                        price_unit = vals['base_price']
                        if price_list and price_unit and starting_line:
                            wholesale = self._calculate_wholesale_price(
                                subscription_line, price_unit, price_list)
                        report_data.write(
                            {'wholesale_price': wholesale if wholesale > 0 else 0})
                current_month_start_date = current_month_start_date + \
                    relativedelta(months=1)
                current_month_start_date = current_month_start_date.replace(
                    day=1)
            budget_month = int(params.get_param('budget_month')) or False
        all_report_data = report_data_table.search(
            []).filtered(lambda x: x.date > self.end_date)
        if all_report_data:
            all_report_data.unlink()
        all_report_data = report_data_table.search(
            []).filtered(lambda x: x.date < self.start_date)
        if all_report_data:
            all_report_data.unlink()
        action = self.env.ref(
            'clx_budget_analysis_report.sale_budget_report_action').read()[0]
        return action


class qweb_sale_subscription_budgets_report(models.AbstractModel):
    _name = 'report.clx_budget_analysis_report.report_budget_qweb'

    @api.model
    def _get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name(
            'sale_subscription.budgets_report')
        subscriptions = self.env['sale.subscription.report.data'].search([])
        subscriptions_gouped = {}
        all_periods = []
        for subscription in subscriptions:
            if subscription.partner_id.id not in subscriptions_gouped:
                subscriptions_gouped[subscription.partner_id.id] = {
                    'partner_id': subscription.partner_id.id,
                    'company_name': subscription.company_name,
                }

            if 'subs' not in subscriptions_gouped[subscription.partner_id.id]:
                subscriptions_gouped[subscription.partner_id.id]['subs'] = {}

            if subscription.subscription_id.id not in subscriptions_gouped[subscription.partner_id.id]['subs']:
                subscriptions_gouped[subscription.partner_id.id]['subs'][subscription.subscription_id.id] = {
                    'description': subscription.description,
                    'subscription_id': subscription.subscription_id.id
                }

            if subscription.period not in subscriptions_gouped[subscription.partner_id.id]['subs'][subscription.subscription_id.id]:
                subscriptions_gouped[subscription.partner_id.id]['subs'][subscription.subscription_id.id][subscription.period] = [
                ]
                if subscription.period not in all_periods:
                    all_periods.append(subscription.period)

            subscriptions_gouped[subscription.partner_id.id]['subs'][subscription.subscription_id.id][subscription.period].append(
                {'retail_price': subscription.retail_price,
                 'wholesale_price': subscription.wholesale_price,
                 'management_fee': subscription.management_fee,
                 'start_date': subscription.start_date,
                 'end_date': subscription.end_date})

        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': self,
            'all_periods': all_periods,
            'companies': subscriptions_gouped,
            'get_all': self.get_all,
            # 'print_data': self.print_data,
            # 'get_qty_done_sum': self.get_qty_done_sum,
        }
        return docargs

    @api.model
    def get_all(self):
        data = self._cr.execute("""SELECT sbl.id,sbl.start_date as start_date,
            sbl.product_id as product_id,
            sbl.subscription_id as subscription_id,
            sbl.subscription_line_id as subscription_line_id,
            sbl.management_fee as management_fee,
            sbl.partner_id as partner_id,
            sbl.wholesale_price as wholesale_price,
            sbl.retail_price as price,
            sbl.end_date as end_date
            from sale_subscription_report_data AS sbl group by sbl.partner_id,sbl.id""")
        result = self._cr.fetchall()
        return result


class sale_subscription_budgets_report(models.AbstractModel):
    _name = 'report.sale_subscription.budgets_report'

    @api.model
    def get_html(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name(
            'sale_subscription.budgets_report')
        spk = self.env['sale.subscription.report.data'].search(
            [('id', '=', docids)])
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': self,
            'spk': spk,
            'get_all': self.get_all,
            'print_data': self.print_data,
            'get_qty_done_sum': self.get_qty_done_sum,
        }
        return report_obj.render('sale_reports.report_sale_order_subscription_lines', docargs)

    def get_all(self, para):
        self._cr.execute("""SELECT sbl.id,sbl.start_date as start_date,
            sbl.product_id as product_id,
            sbl.subscription_id as subscription_id,
            sbl.management_fee as management_fee,
            sbl.partner_id as partner_id,
            sbl.wholesale_price as wholesale_price,
            sbl.retail_price as retail_price,
            sbl.period as period
            sbl.end_date as end_date
            from sale_subscription_report_data AS sbl group by sbl.partner_id,sbl.id""" % (para, para))

    def print_data(self, para):
        dict = {}
        list = []
        return list

    def get_qty_done_sum(self, para):

        self._cr.execute("""\
                select sum(retail) from sale_subscription_report_data 
                """ % para)
        return self._cr.fetchall()
