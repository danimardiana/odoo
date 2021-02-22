# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details
from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_send_auto_mail = fields.Boolean(string="Not Send Mail to Followers")

    @api.model
    def set_values(self):
        config_parameter = self.env['ir.config_parameter'].sudo()
        config_parameter.set_param(
            'is_send_auto_mail', self.is_send_auto_mail or False,
        )
        return super(ResConfigSettings, self).set_values()

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update({'is_send_auto_mail': bool(params.get_param('is_send_auto_mail', False))})
        return res
