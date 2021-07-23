# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo.exceptions import ValidationError
from odoo.tools import float_round
from odoo.tools.misc import get_lang

from odoo import api, fields, models, _

terms_and_conditions_default = "Fees based upon minimum guaranteed 6 months. Agreement continues month to month until notice is given. Advertiser or Provider may cancel this agreement by providing 30 day written notice (including notice through email). Invoices are due upon receipt. Prices include creative (two rounds of initial design, changes as needed (ads should run for at least 30 days without changes), campaign management and monthly reports. Branded Search Targeting packages include both desktop and mobile investments."
terms_and_conditions_gs = "Standard Length of Agreement is as selected above. After initial commitment, agreement becomes month to month. Advertiser may cancel this Order and Agreement upon 30 day written notice including notice via email. If cancelled prior to the agreement length, a retroactive setup fee of $250 may be charged. Should Advertiser exercise this right, Advertiser’s liability for further delivery of traffic shall be limited to only that traffic delivered during the 30-day notice period. Launch dates from the 1st-15th will be billed at a full month. Launch dates from the 15th-end of month will be billed a half month. CallChatter invoices are not prorated. Total monthly cost is inclusive of the management fee as defined in the National Preferred Vendor Agreement between Greystar and Conversion Logix."


class ProductPriceCalculation(models.Model):
    _name = "product.price.calculation"
    _description = "Product Price Calculation"

    product_id = fields.Many2one("product.product", string="Product")
    management_fees = fields.Float(string="Management Fees")
    retail_fees = fields.Float(string="Retail Fees")
    wholesale = fields.Float(string="Wholesale")
    order_id = fields.Many2one(related="sale_line_id.order_id")
    sale_line_id = fields.Many2one("sale.order.line", string="Order Line")


class SaleOrder(models.Model):
    _inherit = "sale.order"

    product_price_calculation_ids = fields.One2many(
        "product.price.calculation", "order_id", ondelete="cascade", readonly=True, string="Product Price"
    )
    display_management_fee = fields.Boolean(string="Display Management Fee", default=True)

    def web_base_url(self):
        return self.env["ir.config_parameter"].sudo().get_param("web.base.url")

    def money_formatting(self, val):
        result_string = "${value:.2f}"
        # if result_string [0] != "$"
        return result_string.format(value=val)

    def management_fee_calculation(self, price_unit, product, pricelist):
        pricelist_product = self.env["sale.subscription"].pricelist_determination(product, pricelist)
        result = self.env["sale.subscription"].subscription_wholesale_period(price_unit, pricelist_product)
        return result

    @api.onchange("pricelist_id")
    def onchange_pricelist(self):
        if self.pricelist_id:
            self.display_management_fee = self.pricelist_id.display_management_fee

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        """
        Pricelist will set with current selected customer
        If customer do not with its own pricelist then it will grab form
        its linked contact (Billing Contact) parent price list.
        :return: None
        """
        greystar_flag = (
            self.partner_id.management_company_type_id.name
            and self.partner_id.management_company_type_id.name.find("Greystar") > -1
        )
        super(SaleOrder, self).onchange_partner_id()
        pricelist_id = self.partner_id.property_product_pricelist
        public_plist = self.env.ref("product.list0")
        if pricelist_id == public_plist and self.partner_id.contact_child_ids:
            # contact = self.partner_id.contact_child_ids.filtered(
            #     lambda ch: 'Billing Contact' in ch.mapped(
            #         'contact_type_ids'
            #     ).mapped('name') and ch.child_id.parent_id and
            #                ch.child_id.parent_id.property_product_pricelist
            # )
            contact = self.partner_id.management_company_type_id
            if contact:
                # self.pricelist_id = contact.child_id.parent_id. \
                #     property_product_pricelist.id
                self.pricelist_id = contact.property_product_pricelist.id

        # TOS text populating and Display Management Fee
        if greystar_flag:
            self.note = terms_and_conditions_gs
            self.contract_length = "3_m"
        else:
            self.note = terms_and_conditions_default
            self.contract_length = "1_m"

    def update_price(self):
        """Add Update Price Method to Calculate
        Management Fees and Wholesale fees based on
        Order line Retail Price."""
        for order in self:
            for order_line in order.order_line:
                order_line.update_price()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    # these two fields not in use anymore just lft it for comability

    management_price = fields.Float(string="Management Price")
    wholesale_price = fields.Float(string="Wholesale Price")

    def update_price(self):
        """
        To Calculate Management Fees and Wholesale fees
        based on Order line Retail Price.
        """
        for order_line in self:
            vals = {
                "product_id": order_line.product_id.id,
                "retail_fees": order_line.price_unit,
                "sale_line_id": order_line.id,
            }
            existing_line = order_line.order_id.product_price_calculation_ids.filtered(
                lambda x: x.sale_line_id == order_line
            )
            # Update values on existing line
            if existing_line:
                existing_line.write(vals)
            # Create new line
            else:
                order_line.order_id.product_price_calculation_ids = [(0, 0, vals)]

    def write(self, vals):
        res = super(SaleOrderLine, self).write(vals)
        # update prices on order line updation
        self.update_price()
        return res

    @api.onchange("price_unit")
    def price_unit_change(self):
        if self.price_unit:
            product = self.product_id.with_context(
                lang=get_lang(self.env, self.order_id.partner_id.lang).code,
                partner=self.order_id.partner_id,
                quantity=self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
            )
            products_items = [(product, self.product_uom_qty, self.order_id.partner_id)]
            products = [item[0] for item in products_items]
            categ_ids = {}
            for p in products:
                categ = p.categ_id
                while categ:
                    categ_ids[categ.id] = True
                    categ = categ.parent_id
            categ_ids = list(categ_ids)
            is_product_template = products[0]._name == "product.template"
            if is_product_template:
                prod_tmpl_ids = [tmpl.id for tmpl in products]
                # all variants of all products
                prod_ids = [p.id for p in list(chain.from_iterable([t.product_variant_ids for t in products]))]
            else:
                prod_ids = [product.id for product in products]
                prod_tmpl_ids = [product.product_tmpl_id.id for product in products]
            items = self.order_id.pricelist_id._compute_price_rule_get_items(
                products_items, self.order_id.date_order, self.product_uom.id, prod_tmpl_ids, prod_ids, categ_ids
            )
            for rule in items:
                if is_product_template:
                    if rule.product_tmpl_id and product.id != rule.product_tmpl_id.id:
                        continue
                    if rule.product_id and not (
                        product.product_variant_count == 1 and product.product_variant_id.id == rule.product_id.id
                    ):
                        # product rule acceptable on template if has only one variant
                        continue
                else:
                    if rule.product_tmpl_id and product.product_tmpl_id.id != rule.product_tmpl_id.id:
                        continue
                    if rule.product_id and product.id != rule.product_id.id:
                        continue
                if rule.categ_id:
                    cat = product.categ_id
                    while cat:
                        if cat.id == rule.categ_id.id:
                            break
                        cat = cat.parent_id
                    if not cat:
                        continue
                # pass the condition when user do the upsell and downsell
                if 0 < self.price_unit < rule.min_price and self._context.get("active_model") != "sale.subscription":
                    raise ValidationError(
                        _("Price amount less than Minimum Price. " "It should be greater or equal to %s")
                        % (str(rule.min_price))
                    )
                if rule.base == "pricelist" and rule.base_pricelist_id:
                    # TDE: 0 = price, 1 = rule
                    price_tmp = rule.base_pricelist_id._compute_price_rule([(product, qty, partner)], date, uom_id)[
                        product.id
                    ][0]
                    price = rule.base_pricelist_id.currency_id._convert(
                        price_tmp, self.currency_id, self.env.company, date, round=False
                    )
                else:
                    # if base option is public price take sale price
                    # else cost price of product price_compute returns
                    # the price in the context UoM, i.e. qty_uom_id
                    price = product.price_compute(rule.base)[product.id]
                qty_uom_id = self._context.get("uom") or product.uom_id.id
                price_uom = self.env["uom.uom"].browse([qty_uom_id])
                convert_to_price_uom = lambda price: product.uom_id._compute_price(price, price_uom)
                if price is not False:
                    if rule.compute_price == "fixed":
                        price = convert_to_price_uom(rule.fixed_price)
                    elif rule.compute_price == "percentage":
                        price = (price - price * rule.percent_price / 100) or 0.0
                    else:
                        # complete formula
                        price_limit = price
                        price = (price - (price * (rule.price_discount / 100))) or 0.0
                        if rule.price_round:
                            price = float_round(price, precision_rounding=rule.price_round)
                        if rule.price_surcharge:
                            price_surcharge = convert_to_price_uom(rule.price_surcharge)
                            price += price_surcharge
                        if rule.price_min_margin:
                            price_min_margin = convert_to_price_uom(rule.price_min_margin)
                            price = max(price, price_limit + price_min_margin)
                        if rule.price_max_margin:
                            price_max_margin = convert_to_price_uom(rule.price_max_margin)
                            price = min(price, price_limit + price_max_margin)
                    suitable_rule = rule
                break
