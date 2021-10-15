# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError

from odoo import fields, models, api, _
from . import grouping_data

products_set_grouping_level = grouping_data.products_set_grouping_level


class FakeSaleOrderLine(object):
    def __init__(self, sol, ratio):
        self.order_id = sol.order_id
        self.product_id = sol.product_id
        self.price_unit = sol.price_unit  # * ratio / 100
        self.name = sol.name
        self.parent_id = sol.order_id.partner_id
        self.prorate_amount = sol.prorate_amount  # * ratio / 100
        # self.price_full = sol.price_full * ratio / 100
        self.display_type = sol.display_type
        self.start_date = sol.start_date
        self.end_date = sol.end_date
        self.product_template_id = sol.product_template_id
        self.product_type = sol.product_type
        self.discount = 0
        self._grouping_name_calc = sol.env["sale.order.line"]._grouping_name_calc
        self.co_op_sale_order_line_partner_ids = sol.co_op_sale_order_line_partner_ids

    def __getitem__(self, key):
        # have obj["a"] -> obj.a
        return self.__getattribute__(key)


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

    # co-op clients are presented as fake sales orders for contract calculations
    def contract_data_prepare(
        self,
        start_date,
        sub_lines,
        contract_mode=False,
        partner_id=False,
    ):
        return SaleOrder.contract_data_prepare(self, start_date, sub_lines, contract_mode, partner_id)


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
        return res

    def unlink(self):
        # here was SB's code for
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
                        # product_individual["product_id"] = grouping_rule["product_id"]
                        product_individual["description"] = grouping_rule["description"]
                        if not invoice_level:
                            product_individual["contract_product_description"] = grouping_rule[
                                "contract_product_description"
                            ]

    def contract_data(self, date):
        return_object = {
            "oto_included": False,
            "recurring_included": False,
            "lines__by_dates": [],
        }
        # calculate the last date of SO date processing
        source_lines = self.order_line
        max_date = date
        for line in source_lines:
            start_date = line.start_date
            if line.end_date and line.end_date > max_date:
                max_date = line.end_date
            else:
                start_date = line.start_date
                if line.prorate_amount > 0:
                    start_date += relativedelta(months=1)
                if line.start_date > max_date:
                    max_date = line.start_date
        # while max_date-date
        return return_object

    @staticmethod
    def is_oto_line(start_date, end_date):
        if not end_date:
            return False
        if start_date.year == end_date.year and start_date.month == end_date.month:
            return True
        return False

    @staticmethod
    def collect_oto_spend(initial_array, line):
        result_object = initial_array
        is_oto = SaleOrder.is_oto_line(line["start_date"], line["end_date"])
        period_signature = line["start_date"].strftime("%Y%m")
        start_date = line["start_date"].replace(day=1)

        def update(price, date_signature, date):
            if date_signature not in result_object:
                result_object[date_signature] = {
                    "price": 0.0,
                    "date": date,
                }
            result_object[date_signature]["price"] += price

        if is_oto:
            update(line["price_full"], period_signature, start_date)
        else:
            update(line["price_full"], "recurring_spend", "Recurring")

            if line["price_unit"] and line["is_prorated"]:
                update(line["price_unit"], period_signature, start_date)

        return result_object

    @staticmethod
    def update_recurring_spend(initial_array, line):
        result_object = initial_array
        for date_text in result_object:
            start_date = line["start_date"].replace(day=1)
            if date_text == "recurring_spend" or start_date.strftime("%Y%m") == date_text:
                continue
            if line["prorate_amount"] and line["prorate_amount"] != line["price_unit"]:
                start_date += relativedelta(months=1)
            # if start date == signature this means it was processed already
            if start_date.strftime("%Y%m") == date_text:
                continue
            if result_object[date_text]["date"] >= start_date and (
                not line["end_date"] or result_object[date_text]["date"] <= line["end_date"]
            ):
                result_object[date_text]["price"] += line["price_unit"]

        return result_object

    def contract_data_prepare(self, start_date, lines, contract_mode=True, partner_id=False):
        # check if we have first-month exclusion
        flag_proration = any(map(lambda x: x.prorate_amount, self.order_line))
        start_date_recurring = start_date + relativedelta(months=1)
        if flag_proration:
            initial_month = self._grouping_wrapper(
                start_date=start_date,
                partner_id=partner_id,
                order_line=lines,
                contract_mode=contract_mode,
            )
            recurring_month = self._grouping_wrapper(
                start_date=start_date_recurring,
                partner_id=partner_id,
                order_line=lines,
                contract_mode=contract_mode,
            )
            for product in initial_month:
                if product in recurring_month:
                    initial_month[product]["management_fee_initial"] = initial_month[product]["management_fee"]
                    initial_month[product]["management_fee"] = recurring_month[product]["management_fee"]
            return initial_month.values()
        else:
            return self._grouping_wrapper(
                start_date=start_date, partner_id=partner_id, order_line=lines, contract_mode=contract_mode
            ).values()

    # TODO::
    # True need to pass the partner_id if we going to prorate price value at the contract level
    # parameters: start_date, partner_id, order_line, contract_mode, grouping_levels
    def _grouping_wrapper(self, **kwargs):
        # inputs process
        if not "start_date" in kwargs:
            return []
        start_date = kwargs["start_date"]
        partner_id = kwargs.get("partner_id", False)
        order_line = kwargs.get("order_line", False)
        contract_mode = kwargs.get("contract_mode", False)
        grouping_levels = kwargs.get("grouping_levels", grouping_data.ALL_FLAGS_GROUPING)

        def initial_order_data(line, partner_id):
            price, price_full, coop_coef = self.env["sale.subscription.line"].period_price_calc(
                start_date, partner_id, contract_mode, line
            )
            pricelist2process = self.env["sale.subscription.line"].analytic_account_id.pricelist_determination(
                line.product_id, line.order_id.pricelist_id
            )

            return {
                "order_id": line.order_id,
                "product_name": line.product_id.name,
                "product_variant": line.product_id.product_template_attribute_value_ids.name or "",
                "name": line.name,
                "product_id": line.product_id.id,
                "partner_owner": line.order_id.partner_id,
                "is_prorated": True if line.prorate_amount > 0 else False,
                "price_unit": price,
                "price_full": price_full,
                "coop_coef": coop_coef,
                "pricelist": pricelist2process,
                "category_id": line.product_id.categ_id.id,
                "category_name": line.product_id.categ_id.name,
                "description": line._grouping_name_calc(line)
                if grouping_levels & grouping_data.ACCOUNTING_GROUPING_FLAG
                else line.product_id.categ_id.name,  # second level of grouping - budget wrapping
                "contract_product_description": line.product_id.contract_product_description,
                "display_type": line.display_type,
                "product_template_id": line.product_template_id,
                "discount": 0.0,
                "tax_ids": [],
                "start_date": line.start_date,
                "end_date": False if not line.end_date else line.end_date,
            }

        def last_order_data(product_individual):
            return {
                "product_id": product_individual["product_id"],
                "product_name": product_individual["product_name"],
                "is_prorated": product_individual["is_prorated"],
                "price_unit": product_individual["price_unit"],
                "price_full": product_individual["price_full"],
                "pricelist": product_individual["pricelist"],
                "description": product_individual["description"],
                "contract_product_description": product_individual["contract_product_description"],
                "name": product_individual["name"],
                "category_id": product_individual["category_id"],
                "category_name": product_individual["category_name"],
                "display_type": product_individual["display_type"],
                "product_template_id": product_individual["product_template_id"],
                "start_date": product_individual["start_date"],
                "end_date": product_individual["end_date"],
                "wholesale_price": product_individual["wholesale_price"],
                "management_fee": product_individual["management_fee"],
                "management_fee_product": product_individual["management_fee_product"],
            }

        def last_order_update(product_source, product_additional):
            product_updated = product_source
            product_updated["price_unit"] += product_additional["price_unit"]
            product_updated["price_full"] += product_additional["price_full"]
            product_updated["wholesale_price"] += product_additional["wholesale_price"]
            product_updated["management_fee"] += product_additional["management_fee"]
            product_updated["management_fee_product"] = (
                product_updated["management_fee_product"] or product_additional["management_fee_product"]
            )
            # product_updated["management_fee_calculated"] += product_additional["management_fee_calculated"]
            return product_updated

        source_lines = order_line or self.order_line
        return self.grouping_all_products(
            source_lines,
            partner_id,
            initial_order_data,
            last_order_data,
            last_order_update,
            start_date,
            grouping_levels,
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
    def grouping_all_products(
        self,
        source_lines,
        partner_id,
        initial_obj,
        last_obj_set,
        last_obj_update,
        start_date,
        grouping_levels=grouping_data.ALL_FLAGS_GROUPING,
    ):

        modified_invoice_lines = []
        for line in source_lines:
            line_to_add = initial_obj(line, partner_id)
            modified_invoice_lines.append(line_to_add)

        # grouping by product set
        if grouping_levels & grouping_data.PRODUCT_GROUPING_FLAG:
            self.grouping_by_product_set(modified_invoice_lines)

        # grouping by description
        final_values = {}

        for product_individual in modified_invoice_lines:
            # combine the lines contains the same description, tax and discount
            combined_signature = ",".join(map(lambda tax: str(tax), product_individual["tax_ids"])) + str(
                product_individual["discount"]
            )

            # not take to account the product id when grouping the products belong to the bundles.
            if product_individual["description"] not in [i["description"] for i in products_set_grouping_level]:
                combined_signature += str(product_individual["product_id"])

            if grouping_levels & grouping_data.DESCRIPTION_GROUPING_FLAG:
                combined_signature += product_individual["description"]

            # in case if grouping should take date in to account
            if grouping_levels & grouping_data.DATE_GROUPING_FLAG:
                combined_signature += str(product_individual["start_date"]) + str(product_individual["end_date"])
            product_individual["product_signature"] = combined_signature
            if partner_id.management_fee_grouping:
                product_individual["management_fee_signature"] = str(product_individual["product_id"])
            else:
                product_individual["management_fee_signature"] = combined_signature + str(
                    product_individual["product_id"]
                )

        # update indepedant subscription/quotation lines with calculated Management Fee
        self.update_with_management_fee(modified_invoice_lines, start_date, partner_id)

        for product_individual in modified_invoice_lines:
            combined_signature = product_individual["product_signature"]
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

        return final_values


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