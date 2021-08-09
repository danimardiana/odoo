# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import binascii

from datetime import date
import datetime
from dateutil import parser

from odoo import fields, http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from dateutil.relativedelta import relativedelta
from odoo.osv import expression
from odoo.addons.sale.controllers.portal import CustomerPortal


class CustomerPortal(CustomerPortal):
    @http.route(["/budget_report/<int:client_id>"], type="http", auth="user", website=True)
    def budget_report_view(self, client_id, name=None, signature=None):
        request.env["sale.budget.changes"].with_context({"default_client_id": client_id}).call_the_report()
        report = request.env['ir.actions.report']._get_report_from_name('clx_budget_analysis_report.report_budget_qweb')
        context = dict(request.env.context)
        docids = [131065]
        html = report.with_context(context).render_qweb_html(docids, data=None)[0]
        return request.make_response(html)

