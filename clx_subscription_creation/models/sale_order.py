# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo.exceptions import ValidationError

from odoo import fields, models, api, _
from . import grouping_data

products_set_grouping_level = grouping_data.products_set_grouping_level

class FakeSaleOrderLine:
    def __init__(self, sol, ratio):
        self.order_id = sol.order_id
        self.product_id = sol.product_id
        self.price_unit = sol.price_unit * ratio / 100
        self.name = sol.name
        self.partner_id = sol.product_id
        self.prorate_amount = sol.prorate_amount * ratio / 100
        self.display_type = sol.display_type
        self.product_template_id = sol.product_template_id
        self.product_type = sol.product_type
        self.discount = 0
        self._grouping_name_calc = sol.env["sale.order.line"]._grouping_name_calc


class FakeSaleOrder:
    def append_sale_order_line(self, line, ratio):
        self.order_line.append(FakeSaleOrderLine(line, ratio))

    def __init__(self, so, partner_id):
        self.partner_id = partner_id
        self.partner_invoice_id = so.partner_invoice_id
        self._grouping_wrapper = so.env["sale.order"]._grouping_wrapper
        self.contract_start_date = so.contract_start_date
        self.order_line = []
        self.display_management_fee = False
        self.signature = False
        self.pricelist_id = so.pricelist_id
        # self.money_formatting = so.money_formatting


class SaleOrder(models.Model):
    _inherit = "sale.order"

    contract_start_date = fields.Date(string="Contract Start Date")

    def _prepare_subscription_data(self, template):
        res = super(SaleOrder, self)._prepare_subscription_data(template)
        additional_fields = {
            "initial_sale_order_id": self,
        }
        if self._context.get("is_ratio"):
            partner_id = self._context.get("co_op_partner")
            additional_fields.update(
                {
                    "partner_id": partner_id,
                    "initial_sale_order_id": self,
                    "active": False,
                }
            )
        res.update(additional_fields)
        return res

    def update_existing_subscriptions(self):
        """
        Call super method when upsell is created from the subscription
        otherwise override this method
        """
        # if self.subscription_management == "upsell":
        #     return super(SaleOrder, self).update_existing_subscriptions()
        res = super(SaleOrder, self).update_existing_subscriptions()
        return res
        # temporary paused VLAD, no sence to update subscriptions
        if self.is_ratio:
            print("_________")
            origin = self.origin
            subscription = self.env["sale.subscription"].search([("code", "=", origin)])
            main_sale_order = subscription.recurring_invoice_line_ids[0].so_line_id.order_id
            main_sale_order_line = main_sale_order.order_line.filtered(
                lambda x: x.product_id.id == self.order_line[0].product_id.id
            )
            subscriptions = main_sale_order_line.clx_subscription_ids
            for subscription in subscriptions:
                line_values = self.order_line[0]._update_subscription_line_data(subscription)
                subscription.write({"recurring_invoice_line_ids": line_values})

        #     a = self.env['sale.subscription'].search([('active', '=', False), ('is_co_op', '=', True), (
        #         'partner_id', 'in', self.co_op_sale_order_partner_ids.mapped('partner_id').ids)])
        #     product_id = self.order_line[0].product_id
        #     matched_order_line = main_sale_order.order_line.filtered(lambda x: x.product_id.id == product_id.id)
        #     subscriptions = a.filtered(lambda x: x.id == matched_order_line.subscription_id.id)
        #     print(subscriptions)
        return res

    def create_subscriptions(self):
        """
        override this method because of Create subscription based on sale order line.
        create different subscription from sale order line
        """
        res = []
        sale_subscription_obj = self.env["sale.subscription"].sudo()
        # if not self.is_ratio:
        if self.subscription_management == "create":
            for line in self.order_line.filtered(lambda x: x.product_id.recurring_invoice):
                if not line.product_id.subscription_template_id:
                    raise ValidationError(_("Please select Subscription Template on {}").format(line.product_id.name))
                values = line.order_id._prepare_subscription_data(line.product_id.subscription_template_id)
                values["initial_sale_order_id"] = self.id
                values["recurring_invoice_line_ids"] = line._prepare_subscription_line_data()
                subscription = sale_subscription_obj.create(values)
                # create corresponding co-op lines if exist
                if line.is_co_op and len(line.co_op_sale_order_line_partner_ids) > 0:
                    for coop in line.co_op_sale_order_line_partner_ids:
                        coop_subscription_record = {
                            "partner_id": coop.partner_id.id,
                            "ratio": coop.ratio,
                            "subscription_id": subscription.id,
                        }
                        self.env["co.op.subscription.partner"].create(coop_subscription_record)
                res.append(subscription.id)
                subscription.message_post_with_view(
                    "mail.message_origin_link",
                    values={"self": subscription, "origin": line.order_id},
                    subtype_id=self.env.ref("mail.mt_note").id,
                    author_id=self.env.user.partner_id.id,
                )
                line.subscription_id = subscription.id
        # elif self.is_ratio:
        #     if self.subscription_management == "create":
        #         for co_op_partner in self.co_op_sale_order_partner_ids:
        #             if co_op_partner.partner_id:
        #                 for line in self.order_line.filtered(lambda x: x.product_id.recurring_invoice):
        #                     if not line.product_id.subscription_template_id:
        #                         raise ValidationError(
        #                             _("Please select Subscription Template on {}").format(line.product_id.name)
        #                         )
        #                     values = line.order_id.with_context(
        #                         co_op_partner=co_op_partner.partner_id.id
        #                     )._prepare_subscription_data(line.product_id.subscription_template_id)
        #                     values["recurring_invoice_line_ids"] = line.with_context(
        #                         ratio=co_op_partner.ratio
        #                     )._prepare_subscription_line_data()
        #                     subscription = sale_subscription_obj.create(values)
        #                     res.append(subscription.id)
        #                     subscription.message_post_with_view(
        #                         "mail.message_origin_link",
        #                         values={"self": subscription, "origin": line.order_id},
        #                         subtype_id=self.env.ref("mail.mt_note").id,
        #                         author_id=self.env.user.partner_id.id,
        #                     )
        #                     line.subscription_id = subscription.id
        #                     clx_sub_list = line.clx_subscription_ids.ids
        #                     clx_sub_list.append(subscription.id)
        #                     line.clx_subscription_ids = clx_sub_list
        return res

    def unlink(self):
        budget_lines = self.env["sale.budget.line"].search([("sol_id", "in", self.order_line.ids)])
        if budget_lines:
            budget_lines.unlink()
        subscriptions = False
        for record in self:
            sub_lines = self.env["sale.subscription.line"].search([("so_line_id", "in", record.order_line.ids)])
            if sub_lines:
                subscriptions = sub_lines.mapped("analytic_account_id")
                sub_lines.unlink()
                subscriptions = subscriptions.filtered(lambda x: not x.recurring_invoice_line_ids)
            if subscriptions:
                subscriptions.unlink()
        return super(SaleOrder, self).unlink()

    def grouping_by_product_set(self, product_lines, invoice_level=False):
        def comparing_product_name(product_group, line):
            category_name = self.env["product.category"].browse(line["category_id"]).name
            product_name = self.env["product.product"].browse(line["product_id"]).name
            sale_order_line_description = self.env["sale.order.line"].browse(line["sale_line_ids"]).name
            product_name_with_variant = "%s (%s)" % (
                product_name,
                self.env["sale.order.line"]
                .browse(line["sale_line_ids"])
                .product_id.product_template_attribute_value_ids.name
                or "",
            )
            return product_group == category_name and (
                sale_order_line_description in (product_name, product_name_with_variant)
            )

        # regrouping followig the products_set_grouping_level table
        for grouping_rule in products_set_grouping_level:
            products_counter = len(grouping_rule["products_list"])
            matching_flag = True
            products_process = {}
            for product_group in grouping_rule["products_list"]:
                if invoice_level:
                    products_process[product_group] = list(
                        filter(lambda x: comparing_product_name(product_group, x), product_lines)
                    )
                else:
                    products_process[product_group] = list(
                        filter(
                            lambda x: (
                                product_group == x["category_name"]
                                and x["name"]
                                in (x["product_name"], "%s (%s)" % (x["product_name"], x["product_variant"]))
                            ),
                            product_lines,
                        )
                    )
                if not len(products_process[product_group]):
                    matching_flag = False
            if matching_flag:
                for product_group in grouping_rule["products_list"]:
                    for product_individual in products_process[product_group]:
                        product_individual["description"] = grouping_rule["description"]
                        if not invoice_level:
                            product_individual["contract_product_description"] = grouping_rule[
                                "contract_product_description"
                            ]

    # TODO: need to pass the partner_id if we going to prorate price value at the contract level
    def _grouping_wrapper(self, partner_id=False, order_line=False):
        def initial_order_data(line, partner_id):
            return {
                "order_id": line.order_id,
                "product_name": line.product_id.name,
                "product_variant": line.product_id.product_template_attribute_value_ids.name or "",
                "name": line.name,
                "product_id": line.product_id.id,
                "price_unit": line.price_unit,
                "category_name": line.product_id.categ_id.name,
                "description": line._grouping_name_calc(line),  # second level of grouping - budget wrapping
                "contract_product_description": line.product_id.contract_product_description,
                "display_type": line.display_type,
                "prorate_amount": line.prorate_amount if line.prorate_amount else line.price_unit,
                "product_template_id": line.product_template_id,
                "management_fee_calculated": self.management_fee_calculation(
                    line.price_unit, line.product_template_id, self.pricelist_id
                ),
                "discount": 0.0,
                "tax_ids": [],
            }

        def last_order_data(product_individual):
            return {
                "product_id": product_individual["product_id"],
                "product_name": product_individual["product_name"],
                "price_unit": product_individual["price_unit"],
                "description": product_individual["description"],
                "contract_product_description": product_individual["contract_product_description"],
                "name": product_individual["name"],
                "display_type": product_individual["display_type"],
                "prorate_amount": product_individual["prorate_amount"],
                "product_template_id": product_individual["product_template_id"],
                "management_fee_calculated": product_individual["management_fee_calculated"],
            }

        def last_order_update(product_source, product_additional):
            product_updated = product_source
            product_updated["price_unit"] += product_additional["price_unit"]
            product_updated["prorate_amount"] += product_additional["prorate_amount"]
            product_updated["management_fee_calculated"] += product_additional["management_fee_calculated"]
            return product_updated

        source_lines = order_line or self.order_line
        return self.grouping_all_products(
            source_lines, partner_id, initial_order_data, last_order_data, last_order_update
        )

    def build_communities(self):
        communities = {}

        for so_line in self.order_line:
            if self.is_co_op and len(so_line.co_op_sale_order_line_partner_ids) > 0:
                for community in so_line.co_op_sale_order_line_partner_ids:
                    if community.partner_id.id not in communities:
                        fake_order = FakeSaleOrder(self, community.partner_id)
                        communities[community.partner_id.id] = fake_order
                    communities[community.partner_id.id].append_sale_order_line(so_line, community.ratio)
        return communities

    # main grouping function
    # partner_id - the client we calculating values for (for co-op)
    def grouping_all_products(self, source_lines, partner_id, initial_obj, last_obj_set, last_obj_update):

        modified_invoice_lines = []
        for line in source_lines:
            line_to_add = initial_obj(line, partner_id)
            modified_invoice_lines.append(line_to_add)

        # first level of grouping - product set
        self.grouping_by_product_set(modified_invoice_lines)

        # final grouping by description
        final_values = {}
        for product_individual in modified_invoice_lines:
            # combine the lines contains the same description, tax and discount
            combined_signature = (
                product_individual["description"]
                + ",".join(map(lambda tax: str(tax), product_individual["tax_ids"]))
                + str(product_individual["discount"])
            )
            if combined_signature not in final_values:
                final_values[combined_signature] = last_obj_set(product_individual)
            else:
                final_values[combined_signature] = last_obj_update(final_values[combined_signature], product_individual)
                for unset_fields in ["product_name", "product_id", "category_id"]:
                    if (
                        unset_fields in final_values[combined_signature]
                        and final_values[combined_signature][unset_fields] != product_individual[unset_fields]
                    ):
                        final_values[combined_signature][unset_fields] = False

        return list(final_values.values())


class SaleOrderLine(models.Model):
    """
    Inherited to setup fields like.
        Start & End Date : Shows subscription life
        Origin: It helps to identify that current line is Base/Upsell/Downsell
    """

    _inherit = "sale.order.line"

    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    line_type = fields.Selection(
        [("base", "Base"), ("upsell", "Upsell"), ("downsell", "Downsell")], string="Origin", default="base"
    )

    def write(self, values):
        res = super(SaleOrderLine, self).write(values)
        budget_obj = self.env["sale.budget.line"]
        if values.get("end_date", False):
            end_date = values.get("end_date")
            subscription_lines = self.env["sale.subscription.line"].search([("so_line_id", "=", self.id)])
            if subscription_lines:
                [sub_line.write({"end_date": values.get("end_date")}) for sub_line in subscription_lines]
                for line in subscription_lines:
                    if line.invoice_start_date > self.end_date:
                        line.write({"invoice_start_date": False, "invoice_end_date": False})
                    elif line.invoice_start_date < self.end_date and line.invoice_end_date > self.end_date:
                        line.write({"invoice_end_date": self.end_date})
            budget_lines = budget_obj.search([("sol_id", "=", self.id)])
            if budget_lines:
                [budget_line.write({"end_date": values.get("end_date")}) for budget_line in budget_lines]
        return res

    @api.onchange("start_date", "end_date")
    def onchange_date_validation(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError(_("Invalid date range."))

    def _update_subscription_line_data(self, subscription):
        """
        Prepare a dictionary of values to add or update lines on subscription.
        """
        values = list()
        dict_changes = dict()
        for line in self:
            values.append(line._prepare_subscription_line_data()[0])
        values += [(1, sub_id, {"quantity": dict_changes[sub_id]}) for sub_id in dict_changes]
        return values

    def _prepare_subscription_line_data(self):
        """
        inherited method to set start date and end_date on subscription line
        """
        res = super(SaleOrderLine, self)._prepare_subscription_line_data()
        # if self.order_id.is_ratio:
        #     ratio = self._context.get("ratio")
        #     price_unit = (self.price_unit * ratio) / 100
        #     res[0][-1].update({"price_unit": price_unit})
        res[0][-1].update(
            {
                "start_date": self.start_date,
                "end_date": self.end_date,
                "so_line_id": self.id,
                "line_type": self.line_type,
            }
        )
        if self._context.get("ratio", False):
            res[0][-1].update({"active": False})
        return res

    def unlink(self):
        for record in self:
            subscription_lines = self.env["sale.subscription.line"].search([("so_line_id", "=", record.id)])
            for sub_line in subscription_lines:
                sub_line.unlink()
        return super(SaleOrderLine, self).unlink()