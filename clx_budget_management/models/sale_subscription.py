# -*- coding: utf-8 -*-
import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from collections import OrderedDict
from datetime import timedelta
from odoo import fields, models, api, _


class SaleSubscription(models.Model):
    _inherit = "sale.subscription"

    def create_chatter_log(self, budget_line_id, user):
        if budget_line_id.budget_id and budget_line_id.active:
            budget_line_id.budget_id.message_post(body=_(
                """<p>The <a href=# data-oe-model=sale.order.line
            data-oe-id=%d>%s</a> has been created from <a href=# 
                data-oe-model=sale.order data-oe-id=%d>%s</a>, <a href=# data-oe-model=sale.subscription
                data-oe-id=%d>%s</a> <br/> At : %s <br/> Created by <a href=# 
                data-oe-model=res.users
                data-oe-id=%d>%s</a>
                <br/> Upsell Date : %s <br/>
             Upsell Amount : %s
                .</p>""") % (
                                                           budget_line_id.sol_id.id,
                                                           budget_line_id.sol_id.display_name,
                                                           budget_line_id.sol_id.order_id.id,
                                                           budget_line_id.sol_id.order_id.name,
                                                           budget_line_id.subscription_id.id,
                                                           budget_line_id.subscription_id.code,
                                                           fields.Date.today(),
                                                           user.id,
                                                           user.name,
                                                           budget_line_id.start_date if
                                                           budget_line_id.status ==
                                                           'upsell' else 'NO Upsell',
                                                           budget_line_id.price if
                                                           budget_line_id.status ==
                                                           'upsell' else 0.0
                                                       ))

    def prepared_vals(self, line, sale_budget_created, start_date=False, flag=False):
        """
        prepared vals for create sale budget line
        Param1 : Line - Browsable object of sale order line
        Param2 : sale_budget_created - browsable object of sale budget
        return : return dictionary of sale budget line
        """
        state = "draft"
        active = False
        today = fields.date.today()

        end_date = datetime.date(start_date.year, start_date.month, 1) + relativedelta(months=1,
                                                                                       days=-1)

        subscription_line_id = line.subscription_id.recurring_invoice_line_ids. \
            filtered(lambda x: x.so_line_id.id == line.id)
        base_line = line.subscription_id.recurring_invoice_line_ids.filtered(lambda x: x.line_type == 'base')
        if start_date and end_date and start_date <= today <= end_date:
            state = "active"
            active = True
        elif start_date and end_date and start_date <= today >= end_date:
            state = "closed"
            active = True
        elif start_date and not end_date and start_date <= today:
            state = "active"
            active = True
        wholesale_price = line.wholesale_price
        price_unit = line.price_unit
        if line.order_id.subscription_management in ('upsell', 'downsell') and base_line:
            price_unit = base_line[0].price_unit + price_unit
        price_list = line.order_id.pricelist_id
        if price_list:
            rule = price_list[0].item_ids.filtered(
                lambda x: x.categ_id.id == line.product_id.categ_id.id)
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
                    wholesale_price = price_unit * (
                            (rule.percent_wholesale_price or 0.0) / 100.0)
                if rule.is_wholesale_formula:
                    wholesale_price = price_unit - management_fees
        vals = {
            'start_date': start_date,
            'end_date': end_date,
            'product_id': line.product_id.id,
            'price': line.price_unit,
            'budget_id': sale_budget_created.id if sale_budget_created else False,
            'sol_id': line.id,
            'state': state,
            'active': active,
            'wholesale_price': wholesale_price,
            'subscription_line_id': subscription_line_id.id,
            'product_name': line.product_id.budget_wrapping if line.product_id.budget_wrapping else line.product_id.name
        }
        if line.end_date and start_date <= line.end_date <= end_date and line.end_date.day < 15:
            new_price = line.price_unit / 2
            new_wholesale_price = line.wholesale_price / 2
            vals.update({
                'price': new_price,
                'wholesale_price': new_wholesale_price
            })
        elif line.end_date and start_date > line.end_date:
            vals.update({
                'price': 0.0,
                'wholesale_price': 0.0
            })
        return vals

    def create_or_update_budget_line(self, line, sale_budget):
        """
        this method is used for creating sale budget line
        Param 1 : Order - Browsable object of Sale order
        Param 2 : sale_budget - Browsable object of sale Budget
        Return : No Return
        """
        if not line:
            return self
        cron_id = self.env.ref('clx_budget_management.sale_budget_creation_cron_job')
        user = cron_id.user_id
        budget_line = self.env['sale.budget.line'].search(
            ['|',
             ('active', '=', True),
             ('active', '=', False),
             ]
        )
        params = self.env['ir.config_parameter'].sudo()
        month_selection = int(params.get_param('budget_month')) or False
        if not month_selection and not line.end_date:
            raise ValidationError(_(
                "Please check Configuration of the Month When End date is not set."
            ))
        today = fields.Date.today()
        after_adding_month_date = today + relativedelta(months=month_selection - 1)
        difference_today_end_date = relativedelta(after_adding_month_date, today)
        if line:
            available_budget_line = budget_line.filtered(
                lambda x: x.sol_id.id == line.id)
            if not available_budget_line:
                vals = self.prepared_vals(line, sale_budget, line.start_date)
                subscription_line_id = self.env['sale.subscription.line'].browse(vals.get('subscription_line_id'))
                line_start_date = vals.get('start_date')
                budget_line_id = self.env['sale.budget.line'].create(vals)
                self.create_chatter_log(budget_line_id, user)
                if line.order_id.subscription_management == 'create':
                    if not line.end_date:
                        # month_start_date = datetime.date(datetime.datetime.today().year,
                        #                                  month_selection, 1)
                        # r = relativedelta(month_start_date, line_start_date)
                        month = difference_today_end_date.months
                        if line.product_id.subscription_template_id.recurring_rule_type == 'yearly':
                            month = 11
                        for i in range(0, month):
                            temp = line_start_date.replace(day=1) + relativedelta(months=1)
                            if line.product_id.subscription_template_id.recurring_rule_type == 'yearly':
                                flag = True
                            else:
                                flag = False
                            vals = self.prepared_vals(line, sale_budget, temp, flag)
                            budget_line_id = self.env['sale.budget.line'].create(vals)
                            line_start_date = budget_line_id.start_date
                            self.create_chatter_log(budget_line_id, user)
                    elif line.start_date and line.end_date:
                        r = len(
                            OrderedDict(((line.start_date + timedelta(_)).strftime("%B-%Y"), 0) for _ in
                                        range((line.end_date - line.start_date).days)))
                        if r > 1:
                            for i in range(0, r):
                                temp = line_start_date + relativedelta(months=1)
                                vals = self.prepared_vals(line, sale_budget, temp)
                                budget_line_id = self.env['sale.budget.line'].create(vals)
                                line_start_date = budget_line_id.start_date
                                self.create_chatter_log(budget_line_id, user)

    @api.model
    def _create_sale_budget(self, sale_order=False):
        sale_orders = sale_order
        if not sale_order:
            sale_orders = self.env['sale.order'].search([('state', '=', 'sale')])
        for order in sale_orders:
            sale_budget = self.env['sale.budget'].search(
                [('partner_id', '=', order.partner_id.id), ('state', '=', 'active')], limit=1)
            if order.subscription_management == 'create':
                if sale_budget:
                    for line in order.order_line.filtered(lambda x: x.product_id.recurring_invoice):
                        self.create_or_update_budget_line(line, sale_budget)
                if not sale_budget and any(
                        order.order_line.filtered(lambda x: x.product_id.recurring_invoice)):
                    sale_budget_created = self.env['sale.budget'].create(
                        {'partner_id': order.partner_id.id, 'state': 'active'})
                    if sale_budget_created:
                        for line in order.order_line.filtered(
                                lambda x: x.product_id.recurring_invoice):
                            self.create_or_update_budget_line(line, sale_budget_created)
            else:
                subscription = order.order_line.mapped('subscription_id')
                if subscription and sale_budget:
                    for line in order.order_line.filtered(lambda x: x.product_id.recurring_invoice):
                        self.create_or_update_budget_line(line, sale_budget)
                if not sale_budget and any(
                        order.order_line.filtered(lambda x: x.product_id.recurring_invoice)):
                    sale_budget_created = self.env['sale.budget'].create(
                        {'partner_id': order.partner_id.id, 'state': 'active'})
                    if sale_budget_created:
                        for line in order.order_line.filtered(
                                lambda x: x.product_id.recurring_invoice):
                            self.create_or_update_budget_line(line, sale_budget_created)
