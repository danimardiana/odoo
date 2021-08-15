# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.


from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta
from collections import OrderedDict
from dateutil.relativedelta import relativedelta
import datetime
from calendar import monthrange


class GenerateInvoiceDateRange(models.TransientModel):
    _name = "generate.invoice.date.range"
    _description = "Generate Invoice Date Range"

    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")

    @api.onchange("start_date")
    def onchange_startdate(self):
        self.onchange_date_validation()
        if self.start_date and not self.end_date:
            self.end_date = self.start_date + relativedelta(months=1) + relativedelta(days=-1)

    @api.onchange("end_date")
    def onchange_enddate(self):
        self.onchange_date_validation()

    def onchange_date_validation(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise UserError(_("Invalid date range."))

    def generate_invoice(self):
        result = self.env["sale.subscription"].invoicing_date_range(
            partner_id=self._context.get("active_id"), start_date=self.start_date, end_date=self.end_date
        )

        title = _("Invoicing...")
        if any(result):
            message = _("%s invoices created." % (sum(bool(x) for x in result)))
        else:
            message = _("Nothing to invoice!")

        self.env["bus.bus"].sendone(
            (self._cr.dbname, "res.partner", self.env.user.partner_id.id),
            {
                'type': 'snailmail_invalid_address',
                "title": title,
                "message": message,
                "sticky": False,
            },
        )
        return
