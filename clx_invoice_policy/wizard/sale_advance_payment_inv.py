# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

import itertools

from dateutil import relativedelta
from odoo.exceptions import AccessError

from odoo import models, fields, api


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    invoice_on = fields.Boolean(string="Invoice on")
    invoice_selection = fields.Selection([
        ('prod_categ', 'Product Category'),
        ('sol', 'Sale Order Line')
    ], string="Display on", default="prod_categ")
    is_advanced = fields.Boolean(string="Advanced?")

    @api.model
    def default_get(self, fields):
        vals = super(SaleAdvancePaymentInv, self).default_get(fields)
        if 'is_advanced' in fields:
            sos = self.env['sale.order'].browse(
                self._context.get('active_ids', [])
            )
            vals['is_advanced'] = all([
                s.clx_invoice_policy_id.policy_type == 'advance' for s in sos
            ])
        return vals

    def create_invoices(self):
        if not self.invoice_selection:
            return super(SaleAdvancePaymentInv, self).create_invoices()
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        for order in sale_orders.filtered(lambda x: not x.clx_invoice_policy_id):
            order.with_context(invoice_section='sol')._create_invoices(
                final=self.deduct_down_payments)
        if self.invoice_selection and sale_orders.filtered(lambda x: x.clx_invoice_policy_id):
            if self.invoice_selection == 'sol':
                sale_orders.with_context(invoice_section='sol')._create_invoices(
                    final=self.deduct_down_payments)
            if self.invoice_selection == 'prod_categ':
                act_move = self.env['account.move']
                if not act_move.check_access_rights('create', False):
                    try:
                        self.check_access_rights('write')
                        self.check_access_rule('write')
                    except AccessError:
                        return act_move
                for order in sale_orders.filtered(lambda x: x.clx_invoice_policy_id):
                    invoice_policy = int(order.clx_invoice_policy_id.name.split(' ')[-1]) + 1
                    category = order.order_line.mapped('product_id').mapped('categ_id')
                    invoice_vals = order._prepare_invoice()
                    if invoice_vals:
                        for categ in category:
                            lines = order.order_line.filtered(
                                lambda x: x.product_id.categ_id.id == categ.id and
                                          x.product_id.type == 'service' and
                                          x.product_id.recurring_invoice)
                            for line in lines:
                                line_vals = line._prepare_invoice_line()
                                start_date = line.start_date
                                end_date = line.end_date if line.end_date else start_date + relativedelta.relativedelta(
                                    months=invoice_policy)
                                date_difference = end_date - start_date
                                if date_difference and date_difference.days in (30, 31):
                                    price = line.price_unit
                                else:
                                    price = line.price_unit * invoice_policy
                                line_vals.update({
                                    'category_id': line.product_id.categ_id.id if line.product_id and
                                                                                  line.product_id.categ_id else False,
                                    'sale_line_ids': [(6, 0, lines.ids)],
                                    'price_unit': price
                                })
                                invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
                        temp = invoice_vals.get('invoice_line_ids', False)
                        new_move_line = []
                        tempary_dict = {}
                        category_list = []
                        for key, group in itertools.groupby(
                                temp, lambda item: item[-1]["category_id"]):
                            temp1 = {key: sum([item[-1]["price_unit"] for item in group])}
                            category_list.append(temp1)
                        for vals in invoice_vals.get('invoice_line_ids'):
                            for temp_dict in temp:
                                if temp_dict[-1].get('category_id') == vals[-1].get('category_id'):
                                    if temp_dict[-1].get('category_id') != tempary_dict.get('category_id'):
                                        tempary_dict = temp_dict[-1]
                                        tempary_dict.update({
                                            'product_id': False,
                                            'quantity': 1
                                        })
                                        new_move_line.append((0, 0, tempary_dict))
                        for cat in category_list:
                            for line in new_move_line:
                                if line[-1]['category_id'] == list(cat.keys())[0]:
                                    line[-1]['price_unit'] = list(cat.values())[0]
                        invoice_vals['invoice_line_ids'] = new_move_line
                        act_move.sudo().create(invoice_vals)

        if self._context.get('open_invoices', False):
            return sale_orders.action_view_invoice()
