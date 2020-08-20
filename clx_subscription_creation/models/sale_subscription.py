# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models


class SaleSubscription(models.Model):
    _inherit = "sale.subscription"

    def _get_product_from_line(self):
        """
        set product_id from the recurring invoice line field.
        """
        for subscription in self:
            product_id = subscription.recurring_invoice_line_ids.mapped('product_id')
            subscription.product_id = product_id.id if product_id else False

    product_id = fields.Many2one('product.product', string="Product",
                                 compute='_get_product_from_line')

    def _compute_invoice_count(self):
        invoice = self.env['account.move']
        can_read = invoice.check_access_rights('read', raise_exception=False)
        for subscription in self:
            subscription.invoice_count = can_read and invoice.search_count([
                '|', ('invoice_line_ids.subscription_id', '=', subscription.id),
                ('invoice_line_ids.subscription_ids', 'in', subscription.id)
            ]) or 0

    def action_subscription_invoice(self):
        self.ensure_one()
        invoices = self.env['account.move'].search([
            '|', ('invoice_line_ids.subscription_id', 'in', self.ids),
            ('invoice_line_ids.subscription_ids', 'in', self.id)
        ])
        action = self.env.ref(
            'account.action_move_out_invoice_type').read()[0]
        action["context"] = {"create": False}
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action


class SaleSubscriptionLine(models.Model):
    """
    Inherited to setup fields like.
        Start & End Date : Shows subscription life
        SO Lines: TO link SO line to manage amount
        Origin: It helps to identify that current line is Base/Upsell/Downsell
    """
    _inherit = "sale.subscription.line"

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    so_line_id = fields.Many2one('sale.order.line', string='SO Lines')
    line_type = fields.Selection([
        ('base', 'Base'),
        ('upsell', 'Upsell'),
        ('downsell', 'Downsell')
    ], string='Origin', default='base')
