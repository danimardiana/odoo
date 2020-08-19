# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class SubscriptionHistory(models.Model):
    """
    This model will log history for Customer's Policy/Subscription activities
    """

    _name = 'policy.history'
    _description = "Policy History"
    _order = 'id DESC'

    partner_id = fields.Many2one('res.partner', string="Customer")
    policy_type = fields.Selection([
        ('advance', 'Advanced'),
        ('arrears', 'Arrears'),
    ], string="Policy")
    is_subscribed = fields.Boolean(string="Subscribed?")
    num_of_month = fields.Integer(string="Number Of Months")
