# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo.exceptions import ValidationError

from odoo import models, fields, api, _


class SaleSubscriptionWizard(models.TransientModel):
    _inherit = 'sale.subscription.wizard'

    end_date = fields.Date(string="End Date")

    @api.onchange('date_from', 'end_date')
    def onchange_date_validation(self):
        if self.date_from and self.end_date and \
                self.date_from >= self.end_date:
            raise ValidationError(_("Invalid date range."))

    @api.model
    def default_get(self, fields):
        res = super(SaleSubscriptionWizard, self).default_get(fields)
        subscription = self.env.context['active_id']
        subscription_id = self.env['sale.subscription'].browse(subscription)
        product_id = subscription_id.sudo().recurring_invoice_line_ids[-1].product_id
        if subscription_id and subscription_id.recurring_invoice_line_ids and product_id:
            res['option_lines'] = [(0, 0, {
                'product_id': product_id.id,
                'uom_id': product_id.uom_id.id,
                'name': product_id.description if product_id.description else product_id.name,
            })]
        return res

    def create_sale_order(self):
        """
        inherit this method because of set start date from sale subscription wizard to sale order
        """
        res = super(SaleSubscriptionWizard, self).create_sale_order()
        res_id = res.get('res_id', False)
        if res_id:
            so = self.env['sale.order'].browse(res_id)
            so.onchange_partner_id()
            so.start_date = self.date_from if self.date_from else False
            sol_id = so.order_line.filtered(
                lambda x: x.product_id.id == self.option_lines[0].product_id.id)
            if sol_id:
                price = self.option_lines[0].price
                sol_id.write({
                    'price_unit': price,
                    'product_uom_qty': 1,
                    'start_date': self.date_from,
                    'end_date': self.end_date,
                    'line_type': 'downsell' if price < 0 else 'upsell'
                })
                sol_id.price_unit_change()
            so.update_price()
        return res


class SaleSubscriptionWizardOption(models.TransientModel):
    _inherit = "sale.subscription.wizard.option"

    price = fields.Float(string="Price")
