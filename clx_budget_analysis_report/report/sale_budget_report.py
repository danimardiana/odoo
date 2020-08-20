# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models, tools


class SaleBudgetReport(models.Model):
    """ Sale Budget report """

    _name = "sale.budget.report"
    _auto = False
    _description = "Sale Budget Report"
    _rec_name = "id"

    date = fields.Date('Date', readonly=True)
    product_id = fields.Many2one('product.product', readonly=True)
    subscription_id = fields.Many2one('sale.subscription', readonly=True)
    partner_id = fields.Many2one('res.partner', readonly=True)
    wholesale_price = fields.Float(string='Price')

    def _query(self):
        return """SELECT sbl.id,sbl.start_date as date,
         sbl.product_id as product_id,
         sbl.subscription_id as subscription_id,
         sbl.partner_id as partner_id,
         sbl.price as wholesale_price
        from sale_budget_line AS sbl group by sbl.partner_id,sbl.id"""

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
            )
        """ % (self._table, self._query()))
