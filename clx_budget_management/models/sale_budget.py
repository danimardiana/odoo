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

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('sale.budget')
        return super(SaleBudget, self).create(vals)

    def set_to_close(self):
        if self.sale_budget_ids.filtered(lambda x: x.state == 'active'):
            raise ValidationError(_(
                "There is one Budget line in active State."
            ))
        self.write({'state': 'closed'})


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

    def close_budget_line(self):
        sub_closed_stage = self.env.ref('sale_subscription.sale_subscription_stage_closed')
        for record in self:
            record.state = 'closed'
            record.subscription_id.stage_id = sub_closed_stage.id

    @api.model
    def _change_state_sale_budget_line(self):
        cron_id = self.env.ref(
            'clx_budget_management.sale_budget_line_change_state')
        if cron_id:
            user = cron_id.user_id
        today = fields.Date.today()
        sale_budget_line = self.search([
            ('state', '=', 'draft'),
            ('active', '=', False)
        ])
        for line in sale_budget_line:
            previous_state = line.state
            if line.start_date and line.end_date:
                if line.start_date <= today <= line.end_date:
                    line.state = "active"
                    line.active = True
                if line.start_date <= today >= line.end_date:
                    line.state = "closed"
                    line.active = True
            if line.start_date and not line.end_date and line.start_date <= today:
                line.state = "active"
                line.active = True
            if previous_state != line.state:
                line.budget_id.message_post(body=_(
                    """<p> The <a href=# data-oe-model=sale.order.line
                    data-oe-id=%d>%s</a> has been created from <a href=# data-oe-model=sale.order
                    data-oe-id=%d>%s</a>, <a href=# data-oe-model=sale.subscription
                    data-oe-id=%d>%s</a> <br/> at %s <br/>Created by <a href=# 
                    data-oe-model=res.users
                    data-oe-id=%d>%s</a>.Previous State : %s --> New State : %s <br/> Upsell Date : %s <br/>
                     Upsell Amount : %s
                     </p>"""
                ) % (line.sol_id.id,
                     line.sol_id.display_name,
                     line.sol_id.order_id.id,
                     line.sol_id.order_id.name,
                     line.subscription_id.id,
                     line.subscription_id.code,
                     fields.Date.today(),
                     user.id,
                     user.name,
                     previous_state.capitalize(),
                     line.state.capitalize(),
                     line.start_date if line.status == 'upsell'
                     else False,
                     line.price if line.status == 'upsell'
                     else 0.0))
