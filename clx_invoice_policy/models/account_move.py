# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    mgmt_company = fields.Many2one(related="partner_id.management_company_type_id", store=True)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    category_id = fields.Many2one('product.category', string="Category")
    subscription_ids = fields.Many2many(
        'sale.subscription', string="Subscription(s)")

    management_fees = fields.Float(string="Management Fees")
    retail_price = fields.Float(string="Retails Price")
    wholesale = fields.Float(string="Wholsesale")
