# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ContactType(models.Model):
    _name = "res.partner.clx.child"
    _description = "Partner Children"

    parent_id = fields.Many2one('res.partner')
    child_id = fields.Many2one('res.partner')
    contact_type_ids = fields.Many2many(
        'contact.type', 'contact_type_partner_rel',
        'con_id', 'type_id', string='Contact Type')

    color = fields.Integer(related="child_id.color")
    name = fields.Char(related="child_id.name")
    title = fields.Many2one(related="child_id.title")
    type = fields.Selection(related="child_id.type")
    email = fields.Char(related="child_id.email")
    is_company = fields.Boolean(related="child_id.is_company")
    function = fields.Char(related="child_id.function")
    phone = fields.Char(related="child_id.phone")
    street = fields.Char(related="child_id.street")
    street2 = fields.Char(related="child_id.street2")
    zip = fields.Char(related="child_id.zip")
    city = fields.Char(related="child_id.city")
    country_id = fields.Many2one(related="child_id.country_id")
    mobile = fields.Char(related="child_id.mobile")
    state_id = fields.Many2one(related="child_id.state_id")
    company_id = fields.Many2one(related="child_id.company_id")
    user_id = fields.Many2one(related="child_id.user_id")
    image_128 = fields.Binary(related="child_id.image_128")
    image_1920 = fields.Binary(related="child_id.image_1920")
    lang = fields.Selection(related="child_id.lang")
    comment = fields.Text(related="child_id.comment")
    display_name = fields.Char(related="child_id.display_name")
    contact_display_kanban = fields.Char(
        related="child_id.contact_display_kanban")
