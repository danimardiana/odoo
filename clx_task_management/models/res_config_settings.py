# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details
from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_create_auto_task = fields.Boolean()
    auto_add_main_task_ids = fields.Many2many('main.task', string="Parent Task")

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'auto_create_sub_task', self.is_create_auto_task or False)
        company_id = self.env.user.company_id
        if company_id:
            company_id.auto_add_main_task_ids = self.auto_add_main_task_ids.ids if self.auto_add_main_task_ids else False
        return super(ResConfigSettings, self).set_values()

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        company_id = self.env.user.company_id
        auto_add_main_task_ids = []
        if company_id:
            auto_add_main_task_ids = company_id.auto_add_main_task_ids.ids if company_id.auto_add_main_task_ids else False
        res.update(auto_add_main_task_ids=auto_add_main_task_ids)
        res.update(
            is_create_auto_task=bool(params.get_param('auto_create_sub_task', '')) or False
        )
        return res

class ResConfigSettingsProof(models.TransientModel):
    _inherit = "res.config.settings"

    proofing_email_default = fields.Char(string="Default Proofing Mail")

    @api.model
    def set_values(self):
        config_parameter = self.env["ir.config_parameter"].sudo()
        config_parameter.set_param(
            "proofing_email_default", self.proofing_email_default
        )
        return super(ResConfigSettingsProof, self).set_values()

    @api.model
    def get_values(self):
        res = super(ResConfigSettingsProof, self).get_values()
        params = self.env["ir.config_parameter"].sudo()
        res.update({"proofing_email_default": str(params.get_param("proofing_email_default", ""))})
        return res