# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo.exceptions import ValidationError

from odoo import fields, models, api, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    contract_start_date = fields.Date(string='Contract Start Date')

    def _prepare_subscription_data(self, template):
        res = super(SaleOrder, self)._prepare_subscription_data(template)
        if not self.is_ratio:
            return res
        if self.is_ratio:
            partner_id = self._context.get('co_op_partner')
            res.update({
                'partner_id': partner_id
            })
            return res

    def update_existing_subscriptions(self):
        """
        Call super method when upsell is created from the subscription
        otherwise override this method
        """
        if self.subscription_management == "upsell":
            return super(SaleOrder, self).update_existing_subscriptions()

    def create_subscriptions(self):
        """
        override this method because of Create subscription based on sale order line.
        create different subscription from sale order line
        """
        res = []
        sale_subscription_obj = self.env['sale.subscription'].sudo()
        if not self.is_ratio:
            if self.subscription_management == "create":
                for line in self.order_line.filtered(
                        lambda x: x.product_id.recurring_invoice):
                    if not line.product_id.subscription_template_id:
                        raise ValidationError(_(
                            "Please select Subscription Template on {}"
                        ).format(line.product_id.name))
                    values = line.order_id._prepare_subscription_data(
                        line.product_id.subscription_template_id)
                    values['recurring_invoice_line_ids'] = line._prepare_subscription_line_data()
                    subscription = sale_subscription_obj.create(values)
                    res.append(subscription.id)
                    subscription.message_post_with_view(
                        'mail.message_origin_link',
                        values={'self': subscription, 'origin': line.order_id},
                        subtype_id=self.env.ref('mail.mt_note').id,
                        author_id=self.env.user.partner_id.id
                    )
                    line.subscription_id = subscription.id
        elif self.is_ratio:
            if self.subscription_management == "create":
                for co_op_partner in self.co_op_sale_order_partner_ids:
                    if co_op_partner.partner_id:
                        for line in self.order_line.filtered(
                                lambda x: x.product_id.recurring_invoice):
                            if not line.product_id.subscription_template_id:
                                raise ValidationError(_(
                                    "Please select Subscription Template on {}"
                                ).format(line.product_id.name))
                            values = line.order_id.with_context(
                                co_op_partner=co_op_partner.partner_id.id)._prepare_subscription_data(
                                line.product_id.subscription_template_id)
                            values['recurring_invoice_line_ids'] = line.with_context(
                                ratio=co_op_partner.ratio)._prepare_subscription_line_data()
                            subscription = sale_subscription_obj.create(values)
                            res.append(subscription.id)
                            subscription.message_post_with_view(
                                'mail.message_origin_link',
                                values={'self': subscription, 'origin': line.order_id},
                                subtype_id=self.env.ref('mail.mt_note').id,
                                author_id=self.env.user.partner_id.id
                            )
                            line.subscription_id = subscription.id
                            clx_sub_list = line.clx_subscription_ids.ids
                            clx_sub_list.append(subscription.id)
                            line.clx_subscription_ids = clx_sub_list
        return res

    def unlink(self):
        subscriptions = self.order_line.mapped('subscription_id')
        if subscriptions:
            subscriptions.unlink()
        return super(SaleOrder, self).unlink()


class SaleOrderLine(models.Model):
    """
    Inherited to setup fields like.
        Start & End Date : Shows subscription life
        Origin: It helps to identify that current line is Base/Upsell/Downsell
    """
    _inherit = "sale.order.line"

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    line_type = fields.Selection([
        ('base', 'Base'),
        ('upsell', 'Upsell'),
        ('downsell', 'Downsell')
    ], string='Origin', default='base')

    def write(self, values):
        res = super(SaleOrderLine, self).write(values)
        budget_obj = self.env['sale.budget.line']
        if values.get('end_date', False):
            end_date = values.get('end_date')
            subscription_lines = self.env['sale.subscription.line'].search([('so_line_id', '=', self.id)])
            if subscription_lines:
                [sub_line.write({'end_date': values.get('end_date')}) for sub_line in subscription_lines]
                for line in subscription_lines:
                    if line.invoice_start_date > self.end_date:
                        line.write({
                            'invoice_start_date': False,
                            'invoice_end_date': False
                        })
                    elif line.invoice_start_date < self.end_date and line.invoice_end_date > self.end_date:
                        line.write({
                            'invoice_end_date': self.end_date
                        })
            budget_lines = budget_obj.search([('sol_id', '=', self.id)])
            if budget_lines:
                [budget_line.write({'end_date': values.get('end_date')}) for budget_line in budget_lines]
        return res

    @api.onchange('product_id')
    def onchange_start_date(self):
        if self.product_id and self.order_id.contract_start_date:
            self.start_date = self.order_id.contract_start_date
        elif self.product_id and not self.start_date:
            raise ValidationError(_("Please select start date."))

    @api.onchange('start_date', 'end_date')
    def onchange_date_validation(self):
        if self.start_date and self.end_date and \
                self.start_date >= self.end_date:
            raise ValidationError(_("Invalid date range."))

    def _update_subscription_line_data(self, subscription):
        """
        Prepare a dictionary of values to add or update lines on subscription.
        """
        values = list()
        dict_changes = dict()
        for line in self:
            values.append(line._prepare_subscription_line_data()[0])
        values += [(1, sub_id, {
            'quantity': dict_changes[sub_id]
        }) for sub_id in dict_changes]
        return values

    def _prepare_subscription_line_data(self):
        """
        inherited method to set start date and end_date on subscription line
        """
        res = super(SaleOrderLine, self)._prepare_subscription_line_data()
        if self.order_id.is_ratio:
            ratio = self._context.get('ratio')
            price_unit = (self.price_unit * ratio) / 100
            res[0][-1].update({
                'price_unit': price_unit
            })
        res[0][-1].update({
            'start_date': self.start_date,
            'end_date': self.end_date,
            'so_line_id': self.id,
            'line_type': self.line_type
        })
        return res
