# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models, tools, api


class SaleSubscriptionData(models.Model):
    _name = "sale.subscription.report.data"
    _description = "Sale Subscription Report Data"

    start_date = fields.Date(string='Start Date', readonly=True)
    end_date = fields.Date(string='End Date', readonly=True)
    period = fields.Char(string='Period')
    product_id = fields.Many2one('product.product', readonly=True)
    subscription_id = fields.Many2one('sale.subscription', readonly=True)
    subscription_line_id = fields.Many2one(
        'sale.subscription.line', readonly=True)
    partner_id = fields.Many2one(
        'res.partner', string="Customer", readonly=True)
    wholesale_price = fields.Float(string='Wholesale Price', readonly=True)
    management_fee = fields.Float(string='Management Fee', readonly=True)
    management_fee_product = fields.Many2one('product.product', readonly=True)
    retail_price = fields.Float(string='Retail')
    changes = fields.Text(readonly=True)
    description = fields.Char(readonly=True)
    category = fields.Char(string='Category')
    company_name = fields.Char(string='Company Name')
class SaleBudgetReport(models.Model):
    """ Sale Budget report """

    _name = "sale.budget.report"
    _auto = False
    _description = "Sale Budget Report"
    _rec_name = "id"

    start_date = fields.Date(string='Start Date', readonly=True)
    end_date = fields.Date(string='End Date', readonly=True)
    product_id = fields.Many2one('product.product', readonly=True)
    period = fields.Char(string='Period')
    subscription_id = fields.Many2one('sale.subscription', readonly=True)
    subscription_line_id = fields.Many2one(
        'sale.subscription.line', readonly=True)
    partner_id = fields.Many2one(
        'res.partner', string="Customer", readonly=True)
    wholesale_price = fields.Float(string='Wholesale Price')
    management_fee = fields.Float(string='Management Fee')
    retail_price = fields.Float(string='Retail')
    changes = fields.Text(readonly=True)
    description = fields.Char(readonly=True)
    category = fields.Char(string='Category')
    company_name = fields.Char(string='Company Name')

    def _query(self):
        return """SELECT sbl.id,sbl.period as period,
            sbl.product_id as product_id,
            sbl.subscription_id as subscription_id,
            sbl.subscription_line_id as subscription_line_id,
            sbl.management_fee as management_fee,
            sbl.management_fee_product as management_fee_product,
            sbl.partner_id as partner_id,
            sbl.wholesale_price as wholesale_price,
            sbl.retail_price as retail_price,
            sbl.start_date as start_date,
            sbl.end_date as end_date,   
            sbl.changes as changes,
            sbl.category as category,
            sbl.description as description,
            sbl.company_name as company_name
            from sale_subscription_report_data AS sbl group by sbl.partner_id,sbl.id"""

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
            )
        """ % (self._table, self._query()))
