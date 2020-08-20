# -*- coding: utf-8 -*-
import datetime

from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError

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

    def prepared_vals(self, line, sale_budget_created, start_date=False):
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
            filtered(lambda x: x.product_id.id == line.product_id.id
                               and x.price_unit == line.price_unit
                               and x.start_date == line.start_date)
        if start_date and end_date and start_date <= today <= end_date:
            state = "active"
            active = True
        elif start_date and end_date and start_date <= today >= end_date:
            state = "closed"
            active = True
        elif start_date and not end_date and start_date <= today:
            state = "active"
            active = True
        vals = {
            'start_date': start_date,
            'end_date': end_date,
            'product_id': line.product_id.id,
            'price': line.price_unit,
            'budget_id': sale_budget_created.id if sale_budget_created else False,
            'sol_id': line.id,
            'state': state,
            'active': active,
            'wholesale_price': line.wholesale_price,
            'subscription_line_id': subscription_line_id.id
        }
        return vals

    def create_or_update_budget_line(self, line, sale_budget):
        """
        this method is used for creating sale budget line
        Param 1 : Order - Browsable object of Sale order
        Param 2 : sale_budget - Browsable object of sale Budget
        Return : No Return
        """
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
                "Please check Configuration for Month When End date is not sale."
            ))
        if line:
            available_budget_line = budget_line.filtered(
                lambda x: x.sol_id.id == line.id)
            if not available_budget_line:
                vals = self.prepared_vals(line, sale_budget, line.start_date)
                line_start_date = vals.get('start_date')
                budget_line_id = self.env['sale.budget.line'].create(vals)
                self.create_chatter_log(budget_line_id, user)
                if line.order_id.subscription_management == 'create':
                    if not line.end_date:
                        month_start_date = datetime.date(datetime.datetime.today().year,
                                                         month_selection, 1)
                        r = relativedelta(month_start_date, line_start_date)
                        for i in range(0, r.months):
                            temp = line_start_date + relativedelta(months=1)
                            vals = self.prepared_vals(line, sale_budget, temp)
                            budget_line_id = self.env['sale.budget.line'].create(vals)
                            line_start_date = budget_line_id.start_date
                            self.create_chatter_log(budget_line_id, user)
                    elif line.start_date and line.end_date:
                        difference_start_end_date = relativedelta(line.end_date, line.start_date)
                        for i in range(0, difference_start_end_date.months):
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
        subscription_obj = self.env['sale.subscription']
        for order in sale_orders:
            sale_budget = self.env['sale.budget'].search(
                [('partner_id', '=', order.partner_id.id), ('state', '=', 'active')], limit=1)
            if not order.origin and order.subscription_management == 'create':
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

            if order.origin and order.subscription_management != 'create':
                subscription = subscription_obj.search([('code', '=', order.origin)])
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
