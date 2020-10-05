# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, api, models


class RequestFormAttachments(models.Model):
    _name = 'request.form.attachments'
    _description = 'Request Form Attachments'

    name = fields.Char(string="Name")
    attachment = fields.Binary(string="Attachments")
    req_form_id = fields.Many2one('request.form', string="Request Form")
