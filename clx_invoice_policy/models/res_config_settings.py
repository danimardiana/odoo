# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details
from odoo import fields, models, api

class ResConfigSettingsAPI(models.TransientModel):
    _inherit = "res.config.settings"

    invoices_generate_since = fields.Date(string="Don't generate new invoices before the date:")

    @api.model
    def set_values(self):
        config_parameter = self.env["ir.config_parameter"].sudo()
        config_parameter.set_param("invoices_generate_since", self.invoices_generate_since)
        return super(ResConfigSettingsAPI, self).set_values()

    @api.model
    def get_values(self):
        res = super(ResConfigSettingsAPI, self).get_values()
        params = self.env["ir.config_parameter"].sudo()
        invoices_generate_since_str = params.get_param("invoices_generate_since", False)
        invoices_generate_since = (
            False
            if not fields.Date.to_date(invoices_generate_since_str)
            else fields.Date.to_date(invoices_generate_since_str)
        )
        res.update({"invoices_generate_since": invoices_generate_since})

        return res