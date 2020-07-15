# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang

class ProductPriceCalculation(models.Model):
    _name = "product.price.calculation"

    product_id = fields.Many2one('product.product', string="Product")
    management_fees = fields.Float("Management Fees")
    retail_fees = fields.Float("Retail fees")
    wholesale = fields.Float("Wholesale")
    order_id = fields.Many2one('sale.order')


class SaleOrder(models.Model):
    _inherit = "sale.order"

    product_price_calculation_ids = fields.One2many(
		'product.price.calculation',
		'order_id',
		readonly=True,
		string="Product Price")


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return
        valid_values = self.product_id.product_tmpl_id.valid_product_template_attribute_line_ids.product_template_value_ids
        # remove the is_custom values that don't belong to this template
        for pacv in self.product_custom_attribute_value_ids:
            if pacv.custom_product_template_attribute_value_id not in valid_values:
                self.product_custom_attribute_value_ids -= pacv

        # remove the no_variant attributes that don't belong to this template
        for ptav in self.product_no_variant_attribute_value_ids:
            if ptav._origin not in valid_values:
                self.product_no_variant_attribute_value_ids -= ptav

        vals = {}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = self.product_uom_qty or 1.0

        product = self.product_id.with_context(
            lang=get_lang(self.env, self.order_id.partner_id.lang).code,
            partner=self.order_id.partner_id,
            quantity=vals.get('product_uom_qty') or self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id
        )
        vals.update(name=self.get_sale_order_line_multiline_description_sale(product))

        self._compute_tax_id()

        if self.order_id.pricelist_id and self.order_id.partner_id:
            vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
        self.update(vals)

        # customisation start
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
            prod_ids = [p.id for p in
                        list(chain.from_iterable([t.product_variant_ids for t in products]))]
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
            if rule.min_quantity and self.product_uom_qty < rule.min_quantity:
                continue
            if is_product_template:
                if rule.product_tmpl_id and product.id != rule.product_tmpl_id.id:
                    continue
                if rule.product_id and not (product.product_variant_count == 1 and product.product_variant_id.id == rule.product_id.id):
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
            if rule.min_price > vals['price_unit']:
                raise UserError(_('Price amount less than Minimum Price.'))

            if rule.base == 'pricelist' and rule.base_pricelist_id:
                price_tmp = rule.base_pricelist_id._compute_price_rule([(product, qty, partner)], date, uom_id)[product.id][0]  # TDE: 0 = price, 1 = rule
                price = rule.base_pricelist_id.currency_id._convert(price_tmp, self.currency_id, self.env.company, date, round=False)
            else:
                # if base option is public price take sale price else cost price of product
                # price_compute returns the price in the context UoM, i.e. qty_uom_id
                price = product.price_compute(rule.base)[product.id]

            qty_uom_id = self._context.get('uom') or product.uom_id.id
            price_uom = self.env['uom.uom'].browse([qty_uom_id])
            convert_to_price_uom = (lambda price: product.uom_id._compute_price(price, price_uom))

            if price is not False:
                if rule.compute_price == 'fixed':
                    price = convert_to_price_uom(rule.fixed_price)
                elif rule.compute_price == 'percentage':
                    price = (price - (price * (rule.percent_price / 100))) or 0.0
                else:
                    # complete formula
                    price_limit = price
                    price = (price - (price * (rule.price_discount / 100))) or 0.0
                    if rule.price_round:
                        price = tools.float_round(price, precision_rounding=rule.price_round)

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
            # customisation end

        title = False
        message = False
        result = {}
        warning = {}
        if product.sale_line_warn != 'no-message':
            title = _("Warning for %s") % product.name
            message = product.sale_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            result = {'warning': warning}
            if product.sale_line_warn == 'block':
                self.product_id = False

        return result