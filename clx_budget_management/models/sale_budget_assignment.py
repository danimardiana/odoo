# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

import datetime
from dateutil.relativedelta import relativedelta
from odoo import fields, models


class SaleBudgetChanges(models.Model):
    _name = "sale.budget.assignment"
    _description = "Sale Budget Assignment"

    employees_ids = fields.Many2One('res_users','Users') 
    product_ids = fields.Many2One('res_users','Users') 