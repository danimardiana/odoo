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

    def budget_changes_check(self):
        # in case of global management fee the change of one subscription can affect the other's
        # subscription management fee. So need to check all of them
        partner = self.analytic_account_id.partner_id
        if partner.management_fee_grouping and self.start_date:
            related_subscription_lines = self.env["sale.subscription"].get_subscription_lines(
                partner=partner,
                product=self.product_id,
                start_date=self.start_date,
                exceptions=[self.id],
            )
            for additional_subscription_lines in related_subscription_lines:
                self.env["sale.budget.changes"].refresh_changes(additional_subscription_lines)
        self.env["sale.budget.changes"].refresh_changes(self)

    # hook when subscription lines updated
    def write(self, vals):
        write_result = super().write(vals)
        # updating the sale budget changes. when fields can have influence on
        if [
            value
            for value in vals
            if value in ["start_date", "end_date", "price_unit", "prorate_amount", "prorate_end_amount"]
        ]:
            self.budget_changes_check()
            # updating invoices for invoice policy range only
            self.env["sale.subscription"].invoicing_invoice_policy_range(
                **{
                    "partner": self.analytic_account_id.partner_id,
                }
            )
        return write_result

    def create(self, records):
        create_result = super().create(records)
        # updating the sale budget changes. when fields can have influence on
        for record in create_result:
            record.budget_changes_check()
        return create_result