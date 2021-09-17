# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
# Model to store the Budget Exports
import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from odoo import fields, models, api, _
import base64
import io
import xlsxwriter
import time

class SaleBudgetExports(models.TransientModel):
    _name = "sale.budget.exports"
    _description = "Sale Budget Exports"
    _inherit = ["mail.thread"]
    _order = 'id desc'

    user_id = fields.Many2one("res.users", string="User")
    status = fields.Integer("Status")
    create_date = fields.Datetime(
        string="Create Date"
    )
    start_date = fields.Date(
        string="Start Date"
    )
    end_date = fields.Date(
        string="End Date"
    )
    attachment_name = fields.Char(string="Report Name", readonly=True)
    attachment_file = fields.Binary(string="Report", readonly=True)
    # attachment_id = fields.Many2one('ir.attachment', string="Report", ondelete='cascade', readonly=True)
