# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from datetime import date

from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from odoo import fields, models, api, _
from collections import Counter


class Partner(models.Model):
    _inherit = 'res.partner'

    clx_invoice_policy_id = fields.Many2one(
        'clx.invoice.policy', string="Invoice Policy")
    is_subscribed = fields.Boolean(
        string='Subscribed?', tracking=True, default=True)
    policy_hst_ids = fields.One2many(
        'policy.history', 'partner_id', string="Policy")
    invoice_selection = fields.Selection([
        ('prod_categ', 'Product Category'),
        ('sol', 'Sale Order Line')
    ], string="Display on", default="prod_categ")

    child_invoice_selection = fields.Selection(
        related="management_company_type_id.invoice_selection", string="Display on")

    def generate_invoice_with_date_range(self):
        view_id = self.env.ref('clx_invoice_policy.generate_invoice_date_range_form_view').id
        return {'type': 'ir.actions.act_window',
                'name': _('Generate Invoice Date range'),
                'res_model': 'generate.invoice.date.range',
                'target': 'new',
                'view_mode': 'form',
                'views': [[view_id, 'form']],
                }

    def generate_invoice(self):
        """
        Invoice will be generated for Arrears Policy Type.
        :return: None
        """
        if not self.is_subscribed:
            return self

        lines = self.env['sale.subscription.line'].search([
            ('so_line_id.order_id.partner_id', 'child_of', self.id),
            ('so_line_id.order_id.state', 'in', ('sale', 'done')),
        ])
        if self._context.get('create_invoice_from_wzrd'):
            lines = self.env['sale.subscription.line'].search([
                ('so_line_id.order_id', '=', self._context.get('order')),
            ])
        if not lines:
            return self

        areas_lines = lines.filtered(
            lambda sl: (sl.so_line_id.order_id.clx_invoice_policy_id.policy_type == 'arrears'))
        advance_lines = lines.filtered(
            lambda sl: (sl.so_line_id.order_id.clx_invoice_policy_id.policy_type == 'advance'))
        if areas_lines:
            self.generate_arrears_invoice(areas_lines)
        if advance_lines:
            self.generate_advance_invoice(advance_lines)

    def get_advanced_sub_lines(self, lines):
        """
        To get all the lines which start in Advance month period.
        :param lines: Subscriptions lines
        :return: recordset after merge with advance services
        """
        ad_lines = self.env['sale.subscription.line']
        today = date.today()
        for line in lines:
            policy_month = line.so_line_id.order_id.clx_invoice_policy_id.num_of_month
            end_date = today + relativedelta(
                months=policy_month + 1, days=-1)
            if line.invoice_start_date and line.invoice_start_date < end_date:
                ad_lines += line
        return ad_lines

    def generate_advance_invoice(self, lines):
        """
        To calculate invoice lines for Advances Policy.
        """

        today = date.today()
        yearly_lines = lines.filtered(lambda
                                          x: x.product_id.subscription_template_id and x.product_id.subscription_template_id.recurring_rule_type == 'yearly')
        yearly_lines = yearly_lines.filtered(
            lambda sol: (sol.invoice_start_date and
                         sol.invoice_end_date and
                         sol.invoice_start_date <= today and
                         sol.invoice_end_date >= today
                         ) or (
                                sol.end_date and sol.end_date < today and not sol.last_invoiced and
                                sol.line_type != 'base'
                        )
        )

        yearly_prepared_lines = [line.with_context({
            'advance': True
        })._prepare_invoice_line() for line in yearly_lines]

        lines = lines.filtered(lambda
                                   x: x.product_id.subscription_template_id and x.product_id.subscription_template_id.recurring_rule_type == 'monthly')

        so_lines = lines.filtered(
            lambda sol: (sol.invoice_start_date and
                         sol.invoice_end_date and
                         sol.invoice_start_date <= today and
                         sol.invoice_end_date >= today
                         ) or (
                                sol.end_date and sol.end_date < today and not sol.last_invoiced and
                                sol.line_type != 'base'
                        )
        )
        if self._context.get('from_generate_invoice') and not so_lines:
            so_lines = lines.filtered(
                lambda sol: (sol.invoice_start_date and
                             sol.invoice_end_date and
                             sol.invoice_start_date >= today and
                             sol.invoice_end_date >= today
                             ) or (
                                    sol.end_date and sol.end_date < today and not sol.last_invoiced and
                                    sol.line_type != 'base'
                            )
            )
        if self._context.get('generate_invoice_date_range'):
            so_lines = lines
        if not so_lines and not yearly_lines:
            if self._context.get('from_generate_invoice'):
                raise UserError(_("You must have a sales order to create an invoice"))
            return self
        so_lines |= self.get_advanced_sub_lines(
            lines.filtered(lambda l: l not in so_lines))
        base_lines = {}
        upsell_lines = {}
        downsell_lines = {}
        if self._context.get('create_invoice_from_wzrd'):
            orders = so_lines.mapped('so_line_id').mapped('order_id')
            if not orders:
                return self
            date_order = orders.date_order.date().replace(day=1)
            date_order = date_order + relativedelta(months=1)
            end_date = date_order + relativedelta(months=orders.clx_invoice_policy_id.num_of_month + 1, days=-1)

            so_lines = lines.filtered(
                lambda sol: (sol.invoice_start_date and
                             sol.invoice_end_date and
                             sol.invoice_start_date <= today and
                             sol.invoice_end_date >= today
                             ) or (
                                    sol.end_date and sol.end_date < today and not sol.last_invoiced and
                                    sol.line_type != 'base'
                            )
            )
            prepared_lines = [line.with_context({
                'advance': True,
                'manual': True,
                'end_date': end_date,
                'start_date': date_order,
                'sol': self._context.get('sol')
            })._prepare_invoice_line() for line in so_lines]
        elif self._context.get('cofirm_sale'):
            prepared_lines = [line.with_context({
                'advance': True,
                'cofirm_sale': True
            })._prepare_invoice_line() for line in so_lines]
        elif self._context.get('generate_invoice_date_range'):
            start_date = self._context.get('start_date')
            end_date = self._context.get('end_date')

            prepared_lines = [line.with_context({
                'advance': True,
                'start_date': start_date,
                'end_date': end_date,
                'generate_invoice_date_range': True,
                'regenerate_invoice': self._context.get('regenerate_invoice', False)
            })._prepare_invoice_line() for line in so_lines]
        else:
            prepared_lines = [line.with_context({
                'advance': True
            })._prepare_invoice_line() for line in so_lines]
        if yearly_prepared_lines:
            so_lines = yearly_lines + so_lines
            for y_line in yearly_prepared_lines:
                prepared_lines.append(y_line)

        if not so_lines:
            return self
        if not self._context.get('sol'):
            for line in prepared_lines:
                line_type = line['line_type']
                del line['line_type']
                line['product_id'] = False
                if line_type == 'base':
                    if line['category_id'] not in base_lines:
                        base_lines.update({line['category_id']: line})
                    else:
                        # if line_type != 'base':
                        #     base_lines[line['category_id']]['name'] += "\n%s" % line['name']
                        base_lines[line['category_id']]['quantity'] = 1
                        base_lines[line['category_id']]['discount'] += line['discount']
                        base_lines[line['category_id']]['price_unit'] += line['price_unit']
                        base_lines[line['category_id']]['tax_ids'][0][2].extend(line['tax_ids'][0][2])
                        base_lines[line['category_id']]['analytic_account_id'] = line['analytic_account_id']
                        base_lines[line['category_id']]['analytic_tag_ids'][0][2].extend(line['analytic_tag_ids'][0][2])
                        base_lines[line['category_id']]['subscription_ids'][0][2].extend(line['subscription_ids'][0][2])
                        base_lines[line['category_id']]['management_fees'] += line.get('management_fees')
                        base_lines[line['category_id']]['wholesale'] += line.get('wholesale')

                elif line_type == 'upsell':
                    if line['category_id'] not in upsell_lines:
                        upsell_lines.update({line['category_id']: line})
                    else:
                        # if line_type != 'base':
                        #     base_lines[line['category_id']]['name'] += "\n%s" % line['name']
                        upsell_lines[line['category_id']]['quantity'] = 1
                        upsell_lines[line['category_id']]['discount'] += line['discount']
                        upsell_lines[line['category_id']]['price_unit'] += line['price_unit']
                        upsell_lines[line['category_id']]['tax_ids'][0][2].extend(line['tax_ids'][0][2])
                        upsell_lines[line['category_id']]['analytic_account_id'] = line['analytic_account_id']
                        upsell_lines[line['category_id']]['analytic_tag_ids'][0][2].extend(
                            line['analytic_tag_ids'][0][2])
                        upsell_lines[line['category_id']]['subscription_ids'][0][2].extend(
                            line['subscription_ids'][0][2])
                        base_lines[line['category_id']]['management_fees'] += line.get('management_fees')
                        base_lines[line['category_id']]['wholesale'] += line.get('wholesale')
                elif line_type == 'downsell':
                    if line['category_id'] not in downsell_lines:
                        downsell_lines.update({line['category_id']: line})
                    else:
                        # if line_type != 'base':
                        #     base_lines[line['category_id']]['name'] += "\n%s" % line['name']
                        downsell_lines[line['category_id']]['quantity'] = 1
                        downsell_lines[line['category_id']]['discount'] += line['discount']
                        downsell_lines[line['category_id']]['price_unit'] += line['price_unit']
                        downsell_lines[line['category_id']]['tax_ids'][0][2].extend(line['tax_ids'][0][2])
                        downsell_lines[line['category_id']]['analytic_account_id'] = line['analytic_account_id']
                        downsell_lines[line['category_id']]['analytic_tag_ids'][0][2].extend(
                            line['analytic_tag_ids'][0][2])
                        downsell_lines[line['category_id']]['subscription_ids'][0][2].extend(
                            line['subscription_ids'][0][2])
                        base_lines[line['category_id']]['management_fees'] += line.get('management_fees')
                        base_lines[line['category_id']]['wholesale'] += line.get('wholesale')
            order = so_lines[0].so_line_id.order_id
            final_lines = {}
            if base_lines and upsell_lines:
                for key, val in base_lines.items():
                    for key1, val1 in upsell_lines.items():
                        if key == key1:
                            final_lines.update({
                                key: val
                            })
                            final_lines[key].update({
                                'price_unit': val.get('price_unit') + val1.get('price_unit')
                            })
            vals = {
                'ref': order.client_order_ref,
                'type': 'out_invoice',
                'invoice_origin': '/'.join(so_lines.mapped('so_line_id').mapped('order_id').mapped('name')),
                'invoice_user_id': order.user_id.id,
                'narration': order.note,
                'partner_id': self._context.get('co_op_invoice_partner') if self._context.get(
                    'co_op_invoice_partner') else order.partner_invoice_id.id,
                'fiscal_position_id': order.fiscal_position_id.id or self.property_account_position_id.id,
                'partner_shipping_id': order.partner_shipping_id.id,
                'currency_id': order.pricelist_id.currency_id.id,
                'invoice_payment_ref': order.reference,
                'invoice_payment_term_id': order.payment_term_id.id,
                'invoice_partner_bank_id': order.company_id.partner_id.bank_ids[:1].id,
                'team_id': order.team_id.id,
                'campaign_id': order.campaign_id.id,
                'medium_id': order.medium_id.id,
                'source_id': order.source_id.id,
                'invoice_line_ids': [
                    (0, 0, x) for x in final_lines.values()
                ],
            }
            if final_lines:
                vals.update({
                    'invoice_line_ids': [
                        (0, 0, x) for x in final_lines.values()
                    ]
                })
            else:
                vals.update({
                    'invoice_line_ids':
                        [
                            (0, 0, x) for x in base_lines.values()
                        ] + [
                            (0, 0, x) for x in upsell_lines.values()
                        ] + [
                            (0, 0, x) for x in downsell_lines.values()
                        ],
                })
            account_id = self.env['account.move'].create(vals)
        else:
            order = so_lines[0].so_line_id.order_id
            for line in prepared_lines:
                del line['line_type']
            account_id = self.env['account.move'].create({
                'ref': order.client_order_ref,
                'type': 'out_invoice',
                'invoice_origin': '/'.join(so_lines.mapped('so_line_id').mapped('order_id').mapped('name')),
                'invoice_user_id': order.user_id.id,
                'narration': order.note,
                'partner_id': self._context.get('co_op_invoice_partner') if self._context.get(
                    'co_op_invoice_partner') else order.partner_invoice_id.id,
                'fiscal_position_id': order.fiscal_position_id.id or self.property_account_position_id.id,
                'partner_shipping_id': order.partner_shipping_id.id,
                'currency_id': order.pricelist_id.currency_id.id,
                'invoice_payment_ref': order.reference,
                'invoice_payment_term_id': order.payment_term_id.id,
                'invoice_partner_bank_id': order.company_id.partner_id.bank_ids[:1].id,
                'team_id': order.team_id.id,
                'campaign_id': order.campaign_id.id,
                'medium_id': order.medium_id.id,
                'source_id': order.source_id.id,
                'invoice_line_ids': [(0, 0, x) for x in prepared_lines]
            })
        if account_id:
            account_id.subscription_line_ids = [(6, 0, so_lines.ids)]
            if account_id.partner_id.management_company_type_id.is_flat_discount:
                for line in account_id.invoice_line_ids:
                    for pre_line in prepared_lines:
                        if line.category_id.id == pre_line.get('category_id'):
                            line.price_unit = pre_line.get('price_unit')
                        elif line.product_id and line.product_id.categ_id.id == pre_line.get('category_id'):
                            line.price_unit = pre_line.get('price_unit')

    def generate_arrears_invoice(self, lines):
        today = date.today()
        so_lines = lines.filtered(
            lambda sol: (not sol.end_date or (
                    sol.end_date and sol.end_date >= today
            )) and sol.start_date <= today and (
                                not sol.last_invoiced or
                                sol.last_invoiced.month != today.month)
        )
        if not so_lines:
            if self._context.get('from_generate_invoice'):
                raise UserError(_("You must have a sales order to create an invoice"))
            return self
        invoice_lines = {}

        prepared_lines = [line.with_context({
            'arrears': True
        })._prepare_invoice_line() for line in so_lines]

        if not self._context.get('sol'):
            for line in prepared_lines:
                line_type = line['line_type']
                del line['line_type']
                line['product_id'] = False
                if line['category_id'] not in invoice_lines:
                    invoice_lines.update({line['category_id']: line})
                else:
                    if line_type != 'base':
                        invoice_lines[line['category_id']]['name'] = "\n".join({
                            invoice_lines[line['category_id']]['name'],
                            line['name']
                        })
                    invoice_lines[line['category_id']]['quantity'] = 1
                    invoice_lines[line['category_id']]['discount'] += line['discount']
                    invoice_lines[line['category_id']]['price_unit'] += line['price_unit']
                    invoice_lines[line['category_id']]['tax_ids'][0][2].extend(line['tax_ids'][0][2])
                    invoice_lines[line['category_id']]['analytic_account_id'] = line['analytic_account_id']
                    invoice_lines[line['category_id']]['analytic_tag_ids'][0][2].extend(line['analytic_tag_ids'][0][2])
                    invoice_lines[line['category_id']]['subscription_ids'][0][2].extend(line['subscription_ids'][0][2])
        so_lines.write({
            'last_invoiced': today
        })
        order = so_lines[0].so_line_id.order_id
        vals = {
            'ref': order.client_order_ref,
            'type': 'out_invoice',
            'invoice_origin': '/'.join(
                so_lines.mapped('so_line_id').mapped('order_id').mapped('name')),
            'invoice_user_id': order.user_id.id,
            'narration': order.note,
            'partner_id': self._context.get('co_op_invoice_partner', False) if self._context.get(
                'co_op_invoice_partner', False) else order.partner_invoice_id.id,
            'fiscal_position_id': order.fiscal_position_id.id or self.property_account_position_id.id,
            'partner_shipping_id': order.partner_shipping_id.id,
            'currency_id': order.pricelist_id.currency_id.id,
            'invoice_payment_ref': order.reference,
            'invoice_payment_term_id': order.payment_term_id.id,
            'invoice_partner_bank_id': order.company_id.partner_id.bank_ids[:1].id,
            'team_id': order.team_id.id,
            'campaign_id': order.campaign_id.id,
            'medium_id': order.medium_id.id,
            'source_id': order.source_id.id,
        }
        if not invoice_lines:
            for x in prepared_lines:
                del x['line_type']
                x['quantity'] = 1
            vals.update({
                'invoice_line_ids': [(0, 0, x) for x in prepared_lines]
            })
            self.env['account.move'].create(vals)
        if invoice_lines:
            vals.update({
                'invoice_line_ids': [(0, 0, x) for x in invoice_lines.values()]
            })
            self.env['account.move'].create(vals)

    def log_policy_history(self):
        """
        New history record will be created whenever user changes
        either Policy type or Subscribe/Unsubscribe
        :return: None
        """
        history = []
        for res in self:
            history.append({
                'partner_id': res.id,
                'is_subscribed': res.is_subscribed,
                'policy_type': res.clx_invoice_policy_id.policy_type,
                'num_of_month': res.clx_invoice_policy_id.num_of_month
            })
        self.env['policy.history'].create(history)

    def subscription(self):
        """
        To subscribe and Unsubscribe.
        is_subscribed (Subscribed?) field is used to manage this operation
        :return: None
        """
        for res in self:
            res.is_subscribed = res.env.context.get('subscribe', False)
        self.log_policy_history()

    @api.model
    def create(self, vals):
        res = super(Partner, self).create(vals)
        if vals.get('clx_invoice_policy_id'):
            res.log_policy_history()
        return res

    def write(self, vals):
        res = super(Partner, self).write(vals)
        if vals.get('clx_invoice_policy_id'):
            self.log_policy_history()
        return res

    @api.model
    def _generate_subscription_invoices(self):
        """
        Scheduler Method: To generate invoice at the end of the month
        for those customers who subscribed and has Arrears policy
        :return: Boolean
        """
        customers = self.search([
            ('is_subscribed', '=', True),
            ('clx_invoice_policy_id', '!=', False)
        ])
        if not customers:
            return True
        try:
            for customer in customers:
                customer.generate_invoice()
            return True
        except Exception as e:
            return False
