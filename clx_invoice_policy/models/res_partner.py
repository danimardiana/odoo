# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from datetime import date

from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from odoo import fields, models, api, _
from dateutil import parser
from calendar import monthrange
# from . import grouping_data

# products_set_grouping_level = grouping_data.products_set_grouping_level


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
    ], string="Display on", default="sol")

    invoice_creation_type = fields.Selection([
        ('combined', 'Combined'),
        ('separate', 'Separate')
    ], string="Invoice Creation Type", default="separate")

    child_invoice_selection = fields.Selection(
        related="management_company_type_id.invoice_selection", string="Display on")

    def generate_invoice_with_date_range(self):
        view_id = self.env.ref(
            'clx_invoice_policy.generate_invoice_date_range_form_view').id
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
        if self._context.get('check_invoice_start_date', False):
            advance_lines = advance_lines.filtered(
                lambda sl: (sl.invoice_start_date and sl.invoice_end_date))
        if areas_lines:
            self.generate_arrears_invoice(areas_lines)
        if advance_lines:
            advance_lines = lines.filtered(
                lambda x: x.invoice_start_date and x.invoice_end_date and x.line_type == 'base')
            not_base_lines = lines.filtered(
                lambda x: x.invoice_start_date and x.invoice_end_date and x.line_type != 'base')
            new_advance_lines = []
            invoice_lines = self.invoice_ids.invoice_line_ids
            if invoice_lines and any(line.move_id.state == 'cancel' for line in invoice_lines):
                a = advance_lines.ids
                for invoice_line in invoice_lines:
                    if "Invoicing period" in invoice_line.name:
                        start_date = invoice_line.name.split(
                            ':')[-1].split('-')[0]
                        start_date = parser.parse(start_date)
                        new_line = advance_lines.filtered(
                            lambda x: x.product_id.categ_id.id == invoice_line.category_id.id
                            and x.invoice_start_date == start_date.date()
                            and invoice_line.move_id.state == 'draft')
                        if new_line and new_line[0].id in a:
                            a.remove(new_line[0].id)
                            start = new_line[0].invoice_start_date + \
                                relativedelta(months=1)
                            end = start.replace(day=monthrange(
                                start.year, start.month)[1])
                            new_line[0].invoice_start_date = start
                            new_line[0].invoice_end_date = end
                if a:
                    advance_lines = self.env['sale.subscription.line'].browse(
                        a)
            advance_lines = advance_lines + not_base_lines
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

    def _merge_line_same_description(self, prepared_lines):
        base_lines = {}
        if prepared_lines:
            for line in prepared_lines:
                if line['description'] not in base_lines:
                    base_lines.update({line['description']: line})
                else:
                    base_lines[line['description']]['quantity'] = 1
                    base_lines[line['description']]['price_unit'] += line['price_unit']
                    base_lines[line['description']]['tax_ids'][0][2].extend(line['tax_ids'][0][2])
                    base_lines[line['description']]['analytic_account_id'] = line['analytic_account_id']
                    base_lines[line['description']]['analytic_tag_ids'][0][2].extend(line['analytic_tag_ids'][0][2])
                    base_lines[line['description']]['subscription_ids'][0][2].extend(line['subscription_ids'][0][2])
                    base_lines[line['description']]['subscription_lines_ids'].extend(line['subscription_lines_ids'])
        return base_lines

    def update_rebate_discount(self, draft_inv):
        """
        this method is used for the update rebate discount line value per invoice
        :param draft_inv: recordset of the account.move (draft invoice)
        :return:
        """
        discount_line = {}
        if draft_inv:
            for draft_invoice in draft_inv:
                receivable_line_debit = False
                total_discount = 0.0
                for inv_line in draft_invoice.invoice_line_ids.filtered(lambda x: "Rebate" not in x.name):
                    if self.management_company_type_id:
                        flat_discount = self.management_company_type_id.flat_discount
                        if self.management_company_type_id.is_flat_discount and self.management_company_type_id.clx_category_id and inv_line.category_id.id == self.management_company_type_id.clx_category_id.id:
                            total_discount += flat_discount
                        else:
                            total_discount += (
                                                      inv_line.price_unit * self.management_company_type_id.discount_on_order_line) / 100
                if total_discount:
                    rebate_line = draft_invoice.invoice_line_ids.filtered(lambda x: "Rebate" in x.name)
                    receivable_line = draft_invoice.line_ids.filtered(
                        lambda x: x.account_id.id == draft_invoice.partner_id.property_account_receivable_id.id)
                    if rebate_line:
                        receivable_line_debit = rebate_line.debit
                        self.env.cr.execute(
                            "DELETE FROM account_move_line WHERE id = %s",
                            (rebate_line.id,))
                    discount_line.update({'price_unit': -abs(total_discount),
                                          'category_id': False,
                                          'product_uom_id': False,
                                          'subscription_id': False,
                                          'subscription_ids': False,
                                          'sale_line_ids': False,
                                          'subscription_lines_ids': False,
                                          'name': "Rebate Discount",
                                          'subscription_start_date': False,
                                          'subscription_end_date': False,
                                          'tax_ids': False,
                                          'product_id': False,
                                          'description': "Rebate Discount"
                                          })
                    draft_invoice.with_context(check_move_validity=False, name="name").write(
                        {'invoice_line_ids': [(0, 0, discount_line)]})
                    if receivable_line:
                        receivable_line.debit += receivable_line_debit
                    # draft_invoice._onchange_recompute_dynamic_lines()
                    # draft_invoice._inverse_amount_total()

    def add_discount_line(self, invoice_line_ids):
        """
        add discount line in invoices
        :param invoice_line_ids: list of dictionary of invoice lines.
        :return: discount line (type Dictionary)
        """
        total_discount = 0.0
        discount_line = invoice_line_ids[0][-1].copy()
        for inv_val in invoice_line_ids:
            if self.management_company_type_id:
                flat_discount = self.management_company_type_id.flat_discount
                if self.management_company_type_id.is_flat_discount and self.management_company_type_id.clx_category_id and inv_val[-1][
                    'category_id'] == self.management_company_type_id.clx_category_id.id:
                    total_discount += flat_discount
                else:
                    total_discount += (inv_val[-1][
                                           'price_unit'] * self.management_company_type_id.discount_on_order_line) / 100
        if total_discount:
            discount_line.update({'price_unit': -abs(total_discount),
                                  'category_id': False,
                                  'product_uom_id': False,
                                  'subscription_id': False,
                                  'subscription_ids': False,
                                  'sale_line_ids': False,
                                  'subscription_lines_ids': False,
                                  'name': "Rebate Discount",
                                  'subscription_start_date': False,
                                  'subscription_end_date': False,
                                  'tax_ids': False,
                                  'product_id': False,
                                  'description': "Rebate Discount"
                                  })
            return discount_line

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
        if self._context.get('cofirm_sale', False):
            yearly_lines = lines.filtered(lambda
                                          x: x.product_id.subscription_template_id and x.product_id.subscription_template_id.recurring_rule_type == 'yearly')
        if self._context.get('generate_invoice_date_range', False):
            yearly_lines = lines.filtered(lambda
                                          x: x.product_id.subscription_template_id and x.product_id.subscription_template_id.recurring_rule_type == 'yearly')
        yearly_prepared_lines = [line.with_context({
            'advance': True
        })._prepare_invoice_line() for line in yearly_lines]

        so_lines = lines.filtered(lambda
                                  x: x.product_id.subscription_template_id and x.product_id.subscription_template_id.recurring_rule_type == 'monthly')
        if self._context.get('generate_invoice_date_range'):
            so_lines = lines.filtered(lambda
                                      x: x.product_id.subscription_template_id and x.product_id.subscription_template_id.recurring_rule_type == 'monthly')
        if not so_lines and not yearly_lines:
            if self._context.get('from_generate_invoice'):
                raise UserError(
                    _("You must have a sales order to create an invoice"))
            return self
        base_lines = {}
        upsell_lines = {}
        downsell_lines = {}
        if self._context.get('create_invoice_from_wzrd'):
            orders = so_lines.mapped('so_line_id').mapped('order_id')
            if not orders:
                return self
            prepared_lines = [line.with_context({
                'advance': True,
            })._prepare_invoice_line() for line in so_lines]
        elif self._context.get('cofirm_sale'):
            prepared_lines = [line.with_context({
                'advance': True,
                'cofirm_sale': True
            })._prepare_invoice_line() for line in so_lines]
        elif self._context.get('generate_invoice_date_range'):
            prepared_lines = [line.with_context({
                'advance': True,
                'generate_invoice_date_range': True,
                'start_date': self._context.get('start_date'),
                'end_date': self._context.get('end_date'),
            })._prepare_invoice_line() for line in so_lines]
        else:
            prepared_lines = [line.with_context({
                'advance': True
            })._prepare_invoice_line() for line in so_lines]
        if yearly_prepared_lines:
            so_lines = yearly_lines + so_lines
            for y_line in yearly_prepared_lines:
                prepared_lines.append(y_line)
        for pre_line in prepared_lines:
            sub_lines = so_lines.filtered(lambda x: x.product_id.id == pre_line['product_id'])
            pre_line.update({
                'subscription_lines_ids': sub_lines.ids if sub_lines else False
            })
        # the regrouping lines
        self.env['sale.order'].grouping_by_product_set(prepared_lines, True)
        account_id = False
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
                        base_lines[line['category_id']]['price_unit'] += line['price_unit']
                        base_lines[line['category_id']]['tax_ids'][0][2].extend(line['tax_ids'][0][2])
                        base_lines[line['category_id']]['analytic_account_id'] = line['analytic_account_id']
                        base_lines[line['category_id']]['analytic_tag_ids'][0][2].extend(line['analytic_tag_ids'][0][2])
                        base_lines[line['category_id']]['subscription_ids'][0][2].extend(line['subscription_ids'][0][2])
                        base_lines[line['category_id']]['subscription_lines_ids'].extend(line['subscription_lines_ids'])
                elif line_type == 'upsell':
                    if line['category_id'] not in upsell_lines:
                        upsell_lines.update({line['category_id']: line})
                    else:
                        # if line_type != 'base':
                        #     base_lines[line['category_id']]['name'] += "\n%s" % line['name']
                        upsell_lines[line['category_id']]['quantity'] = 1
                        upsell_lines[line['category_id']]['discount'] = line['discount']
                        upsell_lines[line['category_id']]['price_unit'] += line['price_unit']
                        upsell_lines[line['category_id']]['tax_ids'][0][2].extend(line['tax_ids'][0][2])
                        upsell_lines[line['category_id']]['analytic_account_id'] = line['analytic_account_id']
                        upsell_lines[line['category_id']]['analytic_tag_ids'][0][2].extend(line['analytic_tag_ids'][0][2])
                        upsell_lines[line['category_id']]['subscription_ids'][0][2].extend(line['subscription_ids'][0][2])
                        upsell_lines[line['category_id']]['subscription_lines_ids'].extend(line['subscription_lines_ids'])
                elif line_type == 'downsell':
                    if line['category_id'] not in downsell_lines:
                        downsell_lines.update({line['category_id']: line})
                    else:
                        # if line_type != 'base':
                        #     base_lines[line['category_id']]['name'] += "\n%s" % line['name']
                        downsell_lines[line['category_id']]['quantity'] = 1
                        downsell_lines[line['category_id']]['discount'] = line['discount']
                        downsell_lines[line['category_id']]['price_unit'] += line['price_unit']
                        downsell_lines[line['category_id']]['tax_ids'][0][2].extend(line['tax_ids'][0][2])
                        downsell_lines[line['category_id']]['analytic_account_id'] = line['analytic_account_id']
                        downsell_lines[line['category_id']]['analytic_tag_ids'][0][2].extend(
                            line['analytic_tag_ids'][0][2])
                        downsell_lines[line['category_id']]['subscription_ids'][0][2].extend(
                            line['subscription_ids'][0][2])
                        downsell_lines[line['category_id']]['subscription_lines_ids'].extend(
                            line['subscription_lines_ids'])
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
                                'price_unit': val.get('price_unit') + val1.get('price_unit'),
                                'sale_line_ids': so_lines.mapped('so_line_id'),
                            })
                        else:
                            final_lines.update({
                                key: val
                            })
            if base_lines and downsell_lines:
                for key, val in base_lines.items():
                    for key1, val1 in downsell_lines.items():
                        if key == key1:
                            final_lines.update({
                                key: val
                            })
                            final_lines[key].update({
                                'price_unit': val.get('price_unit') + val1.get('price_unit'),
                                'sale_line_ids': so_lines.mapped('so_line_id'),
                            })
                        else:
                            final_lines.update({
                                key: val
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
            # discount_line = self.add_discount_line(vals['invoice_line_ids'])
            account_move_lines_posted = False
            account_obj = self.env['account.move']
            # if discount_line:
            #     vals['invoice_line_ids'].append((0, 0, discount_line))
            draft_invoices = []
            if all(line[-1]['line_type'] == "downsell" for line in vals['invoice_line_ids']):
                for line in vals['invoice_line_ids']:
                    account_move_lines = self.env['account.move.line'].search(
                        [('partner_id', '=', order.partner_id.id),
                         ('parent_state', '=', 'draft'),
                         ('name', '=', line[-1]['name'])
                         ], limit=1)
                    if account_move_lines and line[-1][
                        'line_type'] == 'downsell' and so_lines.ids not in account_move_lines.subscription_lines_ids.ids:
                        del line[-1]['line_type']
                        draft_invoices.append(account_move_lines.move_id.id)
                        if account_move_lines.move_id:
                            account_move_lines.move_id.with_context(name=line[-1]['name']).write(
                                {'invoice_line_ids': [line]}
                            )
                            move_line = account_move_lines.move_id.invoice_line_ids.filtered(
                                lambda x: x.category_id.id == line[-1]['category_id'] and x.name != line[-1]['name'])
                            if move_line:
                                move_line.write({'name': line[-1]['name']})
                            if account_move_lines.move_id.subscription_line_ids:
                                subscription_lines = account_move_lines.move_id.subscription_line_ids.ids
                                for s_line in so_lines:
                                    subscription_lines.append(s_line.id)
                                account_move_lines.move_id.write(
                                    {'subscription_line_ids': [(6, 0, list(set(subscription_lines)))]})
                    else:
                        # code for the create credit note
                        account_move_lines_posted = self.env['account.move.line'].search(
                            [('partner_id', '=', order.partner_id.id),
                             ('parent_state', '=', 'posted'),
                             ('name', '=', line[-1]['name'])
                             ], limit=1)
                        if account_move_lines_posted:
                            for line in vals['invoice_line_ids']:
                                line[-1]['price_unit'] = abs(line[-1]['price_unit'])
                                if "line_type" in line[-1]:
                                    del line[-1]['line_type']
                # write code for the update rebate discount line for all invoices
                if draft_invoices:
                    draft_invoices = account_obj.browse(draft_invoices)
                    if draft_invoices:
                        self.update_rebate_discount(draft_invoices)
                if account_move_lines_posted:
                    vals.update({
                        'ref': "Reversal of: " + account_move_lines_posted.move_id.name,
                        'type': 'out_refund',
                        'reversed_entry_id': account_move_lines_posted.move_id.id,
                    })
                    discount_line = self.add_discount_line(vals['invoice_line_ids'])
                    if discount_line:
                        vals['invoice_line_ids'].append((0, 0, discount_line))
                    account_id = self.env['account.move'].create(vals)
            else:
                for line in vals['invoice_line_ids']:
                    del line[-1]['line_type']
                discount_line = self.add_discount_line(vals['invoice_line_ids'])
                if discount_line:
                    vals['invoice_line_ids'].append((0, 0, discount_line))
                account_id = self.env['account.move'].create(vals)
            if account_id and account_id.invoice_line_ids:
                for inv_line in account_id.invoice_line_ids:
                    price_list = inv_line.mapped('sale_line_ids').mapped('order_id').mapped('pricelist_id')
                    if price_list:
                        rule = price_list[0].item_ids.filtered(lambda x: x.categ_id.id == inv_line.category_id.id)
                        if rule:
                            percentage_management_price = custom_management_price = 0.0
                            if rule.is_percentage:
                                percentage_management_price = inv_line.price_unit * (
                                        (rule.percent_mgmt_price or 0.0) / 100.0)
                            if rule.is_custom and inv_line.price_unit > rule.min_retail_amount:
                                custom_management_price = inv_line.price_unit * (
                                        (rule.percent_mgmt_price or 0.0) / 100.0)
                            inv_line.management_fees = max(percentage_management_price,
                                                           custom_management_price,
                                                           rule.fixed_mgmt_price)
                            if rule.is_wholesale_percentage:
                                inv_line.wholesale = inv_line.price_unit * (
                                        (rule.percent_wholesale_price or 0.0) / 100.0)
                            if rule.is_wholesale_formula:
                                inv_line.wholesale = inv_line.price_unit - inv_line.management_fees
        else:
            # create invoice as per the order lines
            order = so_lines[0].so_line_id.order_id
            draft_invoices = []
            account_obj = self.env['account.move']
            if all(line['line_type'] == "downsell" for line in prepared_lines):
                # code for the add downsell lines in draft invoice for the same period
                for line in prepared_lines:
                    account_move_lines = self.env['account.move.line'].search(
                        [('partner_id', '=', order.partner_id.id),
                         ('parent_state', '=', 'draft'),
                         ('name', '=', line['name']),
                         ('product_id', '=', line['product_id'])
                         ], limit=1)
                    move_id = account_move_lines.move_id
                    subscription_ids = False
                    if account_move_lines:
                        if 'line_type' in line:
                            del line['line_type']
                        draft_invoices.append(account_move_lines.move_id.id)
                        if account_move_lines.move_id:
                            new_price = account_move_lines.price_unit + line['price_unit']
                            subscription_ids = account_move_lines.mapped('subscription_lines_ids')
                            self.env.cr.execute(
                                "DELETE FROM account_move_line WHERE id = %s",
                                (account_move_lines.id,))
                            account_move_lines._cr.commit()
                            line['price_unit'] = new_price
                            move_id.with_context(check_move_validity=False, name="name").write(
                                {'invoice_line_ids': [(0, 0, line)]})
                    else:
                        move_id.with_context(name=line['name']).write(
                            {'invoice_line_ids': [(0, 0, line)]}
                        )
                    if move_id.invoice_line_ids.subscription_lines_ids:
                        subscription_lines = move_id.invoice_line_ids.subscription_lines_ids.ids
                        if subscription_ids:
                            for s_line in subscription_ids:
                                subscription_lines.append(s_line.id)
                        for s_line in so_lines:
                            subscription_lines.append(s_line.id)
                        move_id.write(
                            {'subscription_line_ids': [(6, 0, list(set(subscription_lines)))]})
                    else:
                        # code for the create credit note
                        account_move_lines_posted = self.env['account.move.line'].search(
                            [('partner_id', '=', order.partner_id.id),
                             ('parent_state', '=', 'posted'),
                             ('name', '=', line['name'])
                             ], limit=1)
                        if account_move_lines_posted:
                            for line in prepared_lines:
                                if 'line_type' in line:
                                    del line['line_type']
                            for line in prepared_lines:
                                line['price_unit'] = abs(line['price_unit'])
                            vals = {
                                'ref': "Reversal of: " + account_move_lines_posted.move_id.name,
                                'type': 'out_refund',
                                'reversed_entry_id': account_move_lines_posted.move_id.id,
                                'invoice_origin': '/'.join(
                                    so_lines.mapped('so_line_id').mapped('order_id').mapped('name')),
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
                                    (0, 0, x) for x in prepared_lines
                                ]
                            }
                            discount_line = self.add_discount_line(vals['invoice_line_ids'])
                            if discount_line:
                                vals['invoice_line_ids'].append((0, 0, discount_line))
                            account_id = self.env['account.move'].create(vals)

                # write code for the update rebate discount line for all invoices
                if draft_invoices:
                    draft_invoices = account_obj.browse(draft_invoices)
                    if draft_invoices:
                        self.update_rebate_discount(draft_invoices)
            else:
                for line in prepared_lines:
                    if 'line_type' in line:
                        del line['line_type']
                if prepared_lines:
                    prepared_lines = self._merge_line_same_description(prepared_lines)
                if self._context.get('cofirm_sale'):
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
                            (0, 0, x) for x in prepared_lines.values()
                        ]
                    }
                    discount_line = self.add_discount_line(vals['invoice_line_ids'])
                    if discount_line:
                        vals['invoice_line_ids'].append((0, 0, discount_line))
                    account_id = self.env['account.move'].create(vals)
                else:
                    # code  for the update draft invoice
                    new_inv_list = []
                    for line in prepared_lines:
                        account_move_lines = self.env['account.move.line'].search(
                            [('partner_id', '=', order.partner_id.id),
                             ('parent_state', '=', 'draft'),
                             ('name', '=', prepared_lines[line]['name']),
                             ('product_id', '=', prepared_lines[line]['product_id'])
                             ], limit=1)
                        move_id = account_move_lines.move_id
                        subscription_ids = False
                        if account_move_lines:
                            if 'line_type' in prepared_lines[line]:
                                del prepared_lines[line]['line_type']
                            draft_invoices.append(account_move_lines.move_id.id)
                            if account_move_lines.move_id:
                                new_price = account_move_lines.price_unit + prepared_lines[line]['price_unit']
                                subscription_ids = account_move_lines.mapped('subscription_lines_ids')
                                self.env.cr.execute(
                                    "DELETE FROM account_move_line WHERE id = %s",
                                    (account_move_lines.id,))
                                account_move_lines._cr.commit()
                                prepared_lines[line]['price_unit'] = new_price
                                move_id.with_context(check_move_validity=False, name="name").write(
                                    {'invoice_line_ids': [(0, 0, prepared_lines[line])]})
                                if move_id.invoice_line_ids.subscription_lines_ids:
                                    subscription_lines = move_id.subscription_line_ids.ids
                                    if subscription_ids:
                                        for s_line in subscription_ids:
                                            subscription_lines.append(s_line.id)
                                    for su_line in so_lines.filtered(
                                            lambda x: x.product_id.id == prepared_lines[line]['product_id']):
                                        subscription_lines.append(su_line.id)
                                    move_id.write(
                                        {'subscription_line_ids': [(6, 0, list(set(subscription_lines)))]})
                        else:
                            new_inv_list.append(prepared_lines[line])
                    if new_inv_list:
                        vals = {
                            'ref': order.client_order_ref,
                            'type': 'out_invoice',
                            'invoice_origin': '/'.join(
                                so_lines.mapped('so_line_id').mapped('order_id').mapped('name')),
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
                                (0, 0, x) for x in new_inv_list
                            ]
                        }
                        discount_line = self.add_discount_line(vals['invoice_line_ids'])
                        if discount_line:
                            vals['invoice_line_ids'].append((0, 0, discount_line))
                        account_id = self.env['account.move'].create(vals)
        if account_id:
            account_id.write({'subscription_line_ids': [(6, 0, so_lines.ids)]})


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
                if 'line_type' in line:
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
        # customers = self.browse(42746)
        if not customers:
            return True
        try:
            for customer in customers:
                try:
                    customer.with_context(check_invoice_start_date=True).generate_invoice()
                except Exception as e:
                    print("-------Error at invoice creation------")
            return True
        except Exception as e:
            return False
    
    def new_generate_invoice(self):
        customers = self.search([
            ('is_subscribed', '=', True),
            ('clx_invoice_policy_id', '!=', False)
        ])
        # customers = self.browse(61427)
        if not customers:
            return True
        for customer in customers:
            start_date = fields.Date.today().replace(day=1)
            end_date = start_date + relativedelta(months=3)
            end_date = end_date + relativedelta(days=-1)
            lang = customer.lang
            format_date = self.env['ir.qweb.field.date'].with_context(
                lang=lang).value_to_html
            all_lines = self.env['sale.subscription.line'].search([
                ('so_line_id.order_id.partner_id', 'child_of', customer.id),
                ('so_line_id.order_id.state', 'in', ('sale', 'done')),
            ])
            all_lines = all_lines.filtered(
                lambda sl: (
                        sl.so_line_id.order_id.clx_invoice_policy_id.policy_type == 'advance' and sl.product_id.subscription_template_id.recurring_rule_type == "monthly"))
            count = len(OrderedDict(((start_date + timedelta(_)).strftime("%B-%Y"), 0) for _ in
                                    range((end_date - start_date).days)))
            next_month_date = start_date
            start_date = start_date
            for i in range(0, count):
                next_month_date = next_month_date + relativedelta(months=1)
                end_date = date(start_date.year, start_date.month,
                                monthrange(start_date.year, start_date.month)[-1])
                final_adv_line = self.env['sale.subscription.line']

                for adv_line in all_lines:
                    if adv_line.product_id.subscription_template_id.recurring_rule_type == "monthly":
                        if not adv_line.end_date and end_date >= adv_line.start_date:
                            final_adv_line += adv_line
                        elif adv_line.end_date and adv_line.start_date <= end_date and start_date <= adv_line.end_date:
                            final_adv_line += adv_line
                advance_lines = final_adv_line
                period_msg = ("Invoicing period: %s - %s") % (
                    format_date(fields.Date.to_string(start_date), {}),
                    format_date(fields.Date.to_string(end_date), {}))
                account_move_lines = self.env['account.move.line'].search(
                    [('partner_id', '=', customer.id), ('name', '=', period_msg),
                     ('parent_state', 'in', ('draft', 'posted')),
                     ('subscription_lines_ids', 'in', advance_lines.ids)])
                if account_move_lines:
                    for ad_line in advance_lines:
                        if ad_line.id in account_move_lines.mapped('move_id').mapped('subscription_line_ids').ids:
                            advance_lines -= ad_line
                if customer.invoice_selection == 'sol':
                    if sum(advance_lines.mapped('price_unit')) < 0:
                        downsell_lines = advance_lines.filtered(lambda x: x.line_type == 'downsell')
                        if downsell_lines:
                            advance_lines -= downsell_lines
                            customer.with_context(generate_invoice_date_range=True, start_date=start_date,
                                                  end_date=end_date, sol=True,
                                                  ).generate_advance_invoice(
                                downsell_lines)
                    customer.with_context(generate_invoice_date_range=True, start_date=start_date,
                                          end_date=end_date, sol=True,
                                          ).generate_advance_invoice(
                        advance_lines)
                else:
                    if sum(advance_lines.mapped('price_unit')) < 0:
                        downsell_lines = advance_lines.filtered(lambda x: x.line_type == 'downsell')
                        if downsell_lines:
                            advance_lines -= downsell_lines
                            customer.with_context(generate_invoice_date_range=True, start_date=start_date,
                                                  end_date=end_date,
                                                  ).generate_advance_invoice(
                                downsell_lines)
                    customer.with_context(generate_invoice_date_range=True, start_date=start_date,
                                          end_date=end_date,
                                          ).generate_advance_invoice(
                        advance_lines)

                for adv_line in all_lines:
                    if adv_line.product_id.subscription_template_id.recurring_rule_type == "yearly" and adv_line.invoice_start_date == next_month_date:
                        advance_lines += adv_line
                    elif adv_line.product_id.subscription_template_id.recurring_rule_type == "yearly":
                        advance_lines -= adv_line
                start_date = start_date + relativedelta(months=1)