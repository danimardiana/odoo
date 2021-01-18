# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, api, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    month_selection = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
        ('6', '6'),
        ('7', '7'),
        ('8', '8'),
        ('9', '9'),
        ('10', '10'),
        ('11', '11'),
        ('12', '12'),
    ], string="Month for Budget Creation")
    team_ids = fields.Many2many('clx.team', string="Teams")

    @api.model
    def set_values(self):
        config_parameter = self.env['ir.config_parameter'].sudo()
        config_parameter.set_param(
            'budget_month', self.month_selection or False,
        )
        company_id = self.env.user.company_id
        if company_id:
            company_id.team_ids = self.team_ids.ids
        return super(ResConfigSettings, self).set_values()

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        company_id = self.env.user.company_id
        team_list = []
        if company_id and company_id.team_ids:
            team_list = company_id.team_ids.ids or []
        res.update(
            month_selection=str(params.get_param('budget_month', '')) or False,
            team_ids=team_list
        )
        return res
