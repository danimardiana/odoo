# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class AdsLink(models.Model):
    _name = "ads.link"
    _description = "Ads Link"

    partner_id = fields.Many2one('res.partner', string="Customer")
    product_id = fields.Many2one('product.product', string="Products")
    category_id = fields.Many2one('product.category', string="Category")
    description = fields.Char(string="Description")
    link = fields.Char(string="Link")
