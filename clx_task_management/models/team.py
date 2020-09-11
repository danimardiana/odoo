# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, api, models


class CLXTeam(models.Model):
    _name = 'clx.team'
    _description = 'CLX Team'
    _rec_name = 'team_name'

    team_name = fields.Char(string='Team')
    team_members_ids = fields.Many2many('res.users', string='Team Members')
