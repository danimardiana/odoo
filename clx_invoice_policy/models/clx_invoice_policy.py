# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models, api


class ClxInvoicePolicy(models.Model):
    _name = 'clx.invoice.policy'
    _description = "Invoice Policy"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name")
    num_of_month = fields.Integer(string="Number Of Months", traking=True)
    policy_type = fields.Selection([
        ('advance', 'Advance'),
        ('arrears', 'Arrears')
    ], string="Policy Type", default="advance", traking=True)

    @api.onchange('num_of_month', 'policy_type')
    def onchange_type(self):
        """
        To compute name of the policy based on policy type and months
        :return: None
        """
        if self.num_of_month or self.policy_type == 'advance':
            self.name = "%s %d" % (
                self.policy_type.capitalize(),
                self.num_of_month
            )
        else:
            self.num_of_month = 0
            self.name = self.policy_type.capitalize()
