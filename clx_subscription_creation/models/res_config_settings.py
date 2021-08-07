# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details
from odoo import fields, models, api

class ResConfigSettingsAPI(models.TransientModel):
    _inherit = "res.config.settings"

    api_token = fields.Char(string="API Access Token")

    @api.model
    def set_values(self):
        config_parameter = self.env["ir.config_parameter"].sudo()
        config_parameter.set_param("api_token", self.api_token)
        return super(ResConfigSettingsAPI, self).set_values()

    @api.model
    def get_values(self):
        res = super(ResConfigSettingsAPI, self).get_values()
        params = self.env["ir.config_parameter"].sudo()
        res.update({"api_token": str(params.get_param("api_token", ""))})
        return res