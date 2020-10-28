# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.


from odoo import models, fields, api


class GenerateInvoiceDateRange(models.TransientModel):
    _name = "generate.invoice.date.range"

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')

    def generate_invoice(self):
        sale_orders = self.env['sale.order'].search([('partner_id', '=', self._context.get('active_id'))])
        if sale_orders:
            print(sale_orders)
