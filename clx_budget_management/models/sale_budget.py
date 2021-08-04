# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo.exceptions import ValidationError

from odoo import fields, models, api, _


class SaleBudget(models.Model):
    _name = "sale.budget"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Sale Budget"

    partner_id = fields.Many2one('res.partner', string="Customer")
    name = fields.Char(string='Name')
    state = fields.Selection([
        ('active', 'Active'),
        ('closed', 'Closed')
    ], string="State", default="active")
    sale_budget_ids = fields.One2many(
        'sale.budget.line', 'budget_id', string="Budget Line")



class SaleBudgetLine(models.Model):
    _name = "sale.budget.line"
    _description = "Sale Budget Line"
    _order = 'sol_id'
    _rec_name = "sol_id"

    budget_id = fields.Many2one(
        'sale.budget', string="Budget", ondelete='cascade')
    start_date = fields.Date(sting="Start Date")
    end_date = fields.Date(sting="End Date")
    price = fields.Float(string="Price")
    partner_id = fields.Many2one('res.partner',
                                 related="budget_id.partner_id", store=True,
                                 readonly=True)
    product_id = fields.Many2one('product.product', string="Product")
    sol_id = fields.Many2one('sale.order.line', string="Sale Order Line")
    status = fields.Selection(
        related="sol_id.order_id.subscription_management", string="Status", store=True,
        readonly=True)
    subscription_id = fields.Many2one(
        'sale.subscription', related="sol_id.subscription_id", store=True, readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed')
    ], string="State")
    active = fields.Boolean(string="Active")
    wholesale_price = fields.Float(string='Wholesale Price')
    subscription_line_id = fields.Many2one('sale.subscription.line', string="Subscription Line")
    product_name = fields.Char(string="Product")
