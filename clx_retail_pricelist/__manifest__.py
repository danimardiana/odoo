# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

{
    'name': 'CLX Retail Pricelist',
    'category': 'Sale',
    'summary': 'To manage pricelist',
    'author': 'CLx Media',
    'website': 'https://conversionlogix.com/',
    'version': '13.1.0.0.9',
    'sequence': 1,
    'license': 'AGPL-3',
    'description': """""",
    'depends': [
        'sale_management',
        'contact_modification',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_category_view.xml',
        'views/product_pricelist_view.xml',
        'views/sale_order_view.xml',
        'report/sale_report_templates.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
