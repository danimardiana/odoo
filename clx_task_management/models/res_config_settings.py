# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details
from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_create_auto_task = fields.Boolean()

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'auto_create_sub_task', self.is_create_auto_task or False)
        return super(ResConfigSettings, self).set_values()

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            is_create_auto_task=bool(params.get_param('auto_create_sub_task', '')) or False
        )
        return res
