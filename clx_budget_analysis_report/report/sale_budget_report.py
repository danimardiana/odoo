# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models, tools, api


class SaleSubscriptionData(models.Model):
    _name = "sale.subscription.report.data"
    _description = "Sale Subscription Report Data"

    date = fields.Date('Date', readonly=True)
    end_date = fields.Date(string='End Date', readonly=True)
    product_id = fields.Many2one('product.product', readonly=True)
    subscription_id = fields.Many2one('sale.subscription', readonly=True)
    subscription_line_id = fields.Many2one('sale.subscription.line', readonly=True)
    partner_id = fields.Many2one('res.partner', string="Customer", readonly=True)
    wholesale_price = fields.Float(string='Wholesale Price', readonly=True)
    price = fields.Float(string='Price', readonly=True)
    base_price = fields.Float(string="Price")
    upsell_down_sell_price = fields.Float(string="Upsell Downsell Price", default=0.0)


class SaleBudgetReport(models.Model):
    """ Sale Budget report """

    _name = "sale.budget.report"
    _auto = False
    _description = "Sale Budget Report"
    _rec_name = "id"

    date = fields.Date('Date', readonly=True)
    end_date = fields.Date(string='End Date', readonly=True)
    product_id = fields.Many2one('product.product', readonly=True)
    subscription_id = fields.Many2one('sale.subscription', readonly=True)
    subscription_line_id = fields.Many2one('sale.subscription.line', readonly=True)
    partner_id = fields.Many2one('res.partner', string="Customer", readonly=True)
    wholesale_price = fields.Float(string='Wholesale Price')
    price = fields.Float(string='Price')
    base_price = fields.Float(readonly=True)
    upsell_down_sell_price = fields.Float(readonly=True)

    def _query(self):
        return """SELECT sbl.id,sbl.date as date,
         sbl.product_id as product_id,
         sbl.subscription_id as subscription_id,
         sbl.subscription_line_id as subscription_line_id,
         sbl.partner_id as partner_id,
         sbl.wholesale_price as wholesale_price,
         sbl.base_price as price,
         sbl.end_date as end_date
        from sale_subscription_report_data AS sbl group by sbl.partner_id,sbl.id"""

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
            )
        """ % (self._table, self._query()))
