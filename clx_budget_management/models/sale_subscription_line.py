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

    # hook when subscription lines updated
    def write(self, vals):
        write_result = super().write(vals)
        # updating the sale budget changes. when fields can have influence on
        if [
            value
            for value in vals
            if value in ["start_date", "end_date", "price_unit", "prorate_amount", "prorate_end_amount"]
        ]:
            self.env["sale.budget.changes"].refresh_changes(self)
        return write_result

    def create(self, records):
        create_result = super().create(records)
        # updating the sale budget changes. when fields can have influence on
        for record in create_result:
            self.env["sale.budget.changes"].refresh_changes(record)
        return create_result