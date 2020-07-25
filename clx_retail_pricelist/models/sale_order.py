# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import float_round
from odoo.tools.misc import get_lang


class ProductPriceCalculation(models.Model):
    _name = "product.price.calculation"
    _description = "Product Price Calculation"

    product_id = fields.Many2one('product.product', string="Product")
    management_fees = fields.Float(string="Management Fees")
    retail_fees = fields.Float(string="Retail Fees")
    wholesale = fields.Float(string="Wholesale")
    order_id = fields.Many2one('sale.order', string="Order")
    sale_line_id = fields.Many2one("sale.order.line", "Order Line")


class SaleOrder(models.Model):
    _inherit = "sale.order"

    product_price_calculation_ids = fields.One2many(
        'product.price.calculation',
        'order_id',
        readonly=True,
        string="Product Price")
    display_management_fee = fields.Boolean(string="Display Management Fee",
                                            default=True)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super(SaleOrder, self).onchange_partner_id()
        pricelist_id = self.partner_id.property_product_pricelist
        public_plist = self.env.ref('product.list0')
        if pricelist_id == public_plist and self.partner_id.contact_child_ids:
            contact = self.partner_id.contact_child_ids.filtered(
                lambda ch: 'Billing Contact' in ch.mapped(
                    'contact_type_ids'
                ).mapped('name') and ch.child_id.parent_id and
                           ch.child_id.parent_id.property_product_pricelist
            )
            if contact:
                self.pricelist_id = contact.child_id.parent_id. \
                    property_product_pricelist.id

    def update_price(self):
        """ Add Update Price Method to Calculate
        Management Fees and Wholesale fees based on
        Order line Retail Price."""
        for order in self:
            for order_line in order.order_line:
                order_line.update_price()

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    management_price = fields.Float(string='Management Price')
    wholesale_price = fields.Float(string='Wholesale Price')

    def update_price(self):
        """ Add Update Price Method to Calculate
        Management Fees and Wholesale fees based on
        Order line Retail Price."""
        for order_line in self:
            vals = {
                'product_id': order_line.product_id.id,
                'retail_fees': order_line.price_unit,
                'management_fees': order_line.management_price,
                'wholesale': order_line.wholesale_price,
                'sale_line_id': order_line.id,
                'order_id': order_line.order_id.id
            }
            existing_line = order_line.order_id.product_price_calculation_ids.filtered(
                lambda x: x.sale_line_id == order_line)
            # Update values on existing line
            if existing_line:
                existing_line.write(vals)
            # Create new line
            else:
                order_line.order_id.product_price_calculation_ids = [(0, 0, vals)]

    @api.model
    def create(self, vals):
        res = super(SaleOrderLine, self).create(vals)
        # update prices on order line creation
        res.update_price()
        return res

    def write(self, vals):
        res = super(SaleOrderLine, self).write(vals)
        # update prices on order line updation
        self.update_price()
        return res

    @api.onchange('price_unit')
    def price_unit_change(self):
        if self.price_unit:
            product = self.product_id.with_context(
                lang=get_lang(self.env, self.order_id.partner_id.lang).code,
                partner=self.order_id.partner_id,
                quantity=self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id
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
                prod_ids = [p.id for p in list(chain.from_iterable([
                    t.product_variant_ids for t in products
                ]))]
            else:
                prod_ids = [product.id for product in products]
                prod_tmpl_ids = [product.product_tmpl_id.id for product in products]
            items = self.order_id.pricelist_id._compute_price_rule_get_items(
                products_items,
                self.order_id.date_order,
                self.product_uom.id,
                prod_tmpl_ids,
                prod_ids,
                categ_ids)
            for rule in items:
                # Calculate management price
                percentage_management_price = custom_management_price = 0.0
                if rule.is_percentage:
                    percentage_management_price = self.price_unit * (
                            (rule.percent_mgmt_price or 0.0) / 100.0)
                if rule.is_custom and self.price_unit > rule.min_retail_amount:
                    custom_management_price = self.price_unit * (
                            (rule.percent_mgmt_price or 0.0) / 100.0)
                self.management_price = max(percentage_management_price,
                                            custom_management_price,
                                            rule.fixed_mgmt_price)
                if rule.is_wholesale_percentage:
                    self.wholesale_price = self.price_unit * (
                            (rule.percent_wholesale_price or 0.0) / 100.0)
                if rule.is_wholesale_formula:
                    self.wholesale_price = self.price_unit - self.management_price
                if is_product_template:
                    if rule.product_tmpl_id and product.id != rule.product_tmpl_id.id:
                        continue
                    if rule.product_id and not (
                            product.product_variant_count == 1 and
                            product.product_variant_id.id == rule.product_id.id
                    ):
                        # product rule acceptable on template if has only one variant
                        continue
                else:
                    if rule.product_tmpl_id and \
                            product.product_tmpl_id.id != rule.product_tmpl_id.id:
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
                if rule.min_price > self.price_unit:
                    raise ValidationError(_(
                        'Price amount less than Minimum Price. '
                        'It should be greater or equal to %s'
                    ) % (str(rule.min_price)))
                if rule.base == 'pricelist' and rule.base_pricelist_id:
                    # TDE: 0 = price, 1 = rule
                    price_tmp = rule.base_pricelist_id._compute_price_rule(
                        [(product, qty, partner)], date, uom_id)[product.id][0]
                    price = rule.base_pricelist_id.currency_id._convert(
                        price_tmp, self.currency_id,
                        self.env.company, date, round=False)
                else:
                    # if base option is public price take sale price
                    # else cost price of product price_compute returns
                    # the price in the context UoM, i.e. qty_uom_id
                    price = product.price_compute(rule.base)[product.id]
                qty_uom_id = self._context.get('uom') or product.uom_id.id
                price_uom = self.env['uom.uom'].browse([qty_uom_id])
                convert_to_price_uom = (
                    lambda price: product.uom_id._compute_price(
                        price, price_uom)
                )
                if price is not False:
                    if rule.compute_price == 'fixed':
                        price = convert_to_price_uom(rule.fixed_price)
                    elif rule.compute_price == 'percentage':
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
