# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

import datetime
from dateutil.relativedelta import relativedelta
from odoo import fields, models


class SaleBudgetChanges(models.Model):
    _name = "sale.budget.changes"
    _description = "Sale Budget Changes"

    subscription_id = fields.Many2one("sale.subscription", string="Subscription")
    partner_id = fields.Many2one("res.partner", related="subscription_id.partner_id", store=True, string="Client")
    product_id = fields.Many2one("product.product", string="Product")
    product_description = fields.Char(string="Product Description")
    category_id = fields.Many2one('product.category', related="subscription_id.product_id.categ_id", store=True,readonly=True, string="Category")
    change_date = fields.Date(sting="Start Date")
    change_price = fields.Float(string="Price")
    change_wholesale = fields.Float(string="Wholesale")
    change_mngmt_fee = fields.Float(string="Management Fee")
    prev_date = fields.Date(sting="Previous Change Date")
    prev_price = fields.Float(string="Previous Price")
    next_date = fields.Date(sting="Next Change Date")
    next_price = fields.Float(string="Next Price")
    status = fields.Selection([("new", "New"), ("closed", "Completed")], string="State", default="new")

    def refresh_changes(self, changed_line):
        date_signature="%Y/%m/%d"
        def is_first_day_of_month(date):
            if date.day == 1:
                return True
            return False

        def is_last_day_of_month(date):
            if date + relativedelta(day=1) == 1:
                return True
            return False

        #mutate the table depending on new/change of price
        def process_change(change_dates_existing, date, change, start_period_date):
            if date in change_dates_existing:
                change_dates_existing[date]["change_price"] += change
            else:
                change_dates_existing[date] = {"change_price": change, 'start_period_date': start_period_date.strftime(date_signature)}

        subscription = changed_line.analytic_account_id
        partner_id = subscription.partner_id
        change_dates_existing = {}
        change_dates_to_update = {}
        periods_spending = {}
        
        # getting existing changes
        current_changes = self.search([("subscription_id.id", "=", subscription.id)])
        for line in current_changes:
            if line.change_date not in change_dates_existing:
                change_dates_existing[line.change_date] = line

        product_id = subscription.product_id
        # todo: possible optimization regarding filter out the old subscription lines
        for line in subscription.recurring_invoice_line_ids:
            start_period_date = line.start_date.replace(day=1)
            start_period_date_text = start_period_date.strftime("%Y/%m/%d")
            # calc spend for whole period
            if start_period_date_text in periods_spending:
                periods_spending[start_period_date_text]["change_price"] += line.period_price_calc(
                    start_period_date, partner_id, True
                )
            else:
                periods_spending[start_period_date_text] = {
                    "change_price": line.period_price_calc(start_period_date, partner_id, True)
                }

            # generating the changes data
            #   starting period
            start_date_text = line.start_date.strftime(date_signature)
            if line["prorate_amount"] != 0:
                process_change(change_dates_to_update, start_date_text, line["prorate_amount"], start_period_date)
                next_period_start = (line.start_date.replace(day=1) + relativedelta(month=1)).strftime(date_signature)
                process_change(change_dates_to_update, next_period_start, line["price_unit"], start_period_date)
            else:
                process_change(change_dates_to_update, start_date_text, line["price_unit"], start_period_date)

            #   ending period
            if line["prorate_end_amount"] != 0:
                process_change(
                    change_dates_to_update,
                    (line.end_date + relativedelta(date=1)).strftime(date_signature),
                    -line["prorate_end_amount"], start_period_date,
                )
                previous_period_end = (line.end_date.replace(day=1) + relativedelta(day=-1)).strftime(date_signature)
                process_change(change_dates_to_update, previous_period_end, -line["price_unit"],start_period_date)
            else:
                process_change(change_dates_to_update, line.end_date.strftime(date_signature), -line["price_unit"],start_period_date)

        pricelist_product = subscription.pricelist_determination(product_id, subscription.pricelist_id)

        # calc wholesale and management fee for periods with changes.
        for period in periods_spending:
            additional_data = subscription.subscription_wholesale_period(
                periods_spending[period]["price"], pricelist_product
            )
            periods_spending[period].update(
                {
                    "management_fee": additional_data["management_fee"],
                    "wholesale": additional_data["wholesale_price"],
                }
            )

        # comparing changes
        sorted_dates = change_dates_to_update.keys().sort()

        # remove changes having the same spending
        for i in range(len(sorted_dates)-1, 0, -1 ):
            if change_dates_to_update[sorted_dates[i-1]]['change_price'] == change_dates_to_update[sorted_dates[i]]['change_price']:
                change_dates_to_update[sorted_dates[i-1]].remove(change_dates_to_update[sorted_dates[i]])
        # clean up existing changes
        for change_date in change_dates_existing:
            if change_date not in sorted_dates:
                self.remove(change_dates_existing[change_date].id);

        for change_date_idx in range(len(sorted_dates)-1, 0, -1 ) :
            # Initial  date need to be passed as Ops team won't have notification about it. 
            # So scan till index 0 excluding 

            change_date = sorted_dates[change_date_idx]
            processing_change = change_dates_to_update[change_date]

            #generate the change object
            period_start_date =  processing_change['start_period_date']
            money_detils = periods_spending[period_start_date]
            next_change = {'price':False,'next_date':False}
            if change_date_idx<len(sorted_dates):
                next_change = {'price':sorted_dates[change_date_idx+1],'next_date':sorted_dates[change_date_idx+1]}
            change_object = {
                    'partner_id' : partner_id,
                    'product_id' : product_id,
                    'product_description' : subscription.description,
                    'change_date' : datetime.datetime.strptime(change_date, date_signature),
                    'change_price' : processing_change['change_price'],
                    'change_wholesale' : money_detils['wholesale'],
                    'change_mngmt_fee' : money_detils['management_fee'],
                    'prev_date' : datetime.datetime.strptime(prev_date, date_signature),
                    'prev_price' : change_dates_to_update[prev_date]['change_price'],
                    'next_date' : next_change,
                    'next_price' : next_change,
                }

            # if chacking date already exist 
            if change_date in change_dates_existing:
                if change_dates_existing[change_date]['change_price'] != processing_change['change_price']:
                    if change_dates_existing[change_date]['change_price'] == change_dates_existing[prev_date]['change_price']:
                        #if prefious changes is same as current one - delete the existing
                        self.delete(change_dates_existing[change_date].id)
                else:
                    change_dates_existing[change_date].update(change_object)
            else:
                self.create(change_object)


            prev_date = change_date

