# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

{
    'name': 'Subscription Creation',
    'version': '13.1.1.0.24',
    'sequence': 1,
    'description': """ Subscription Creation
     - Subscription is created From sale order line
        If sale order line have 2 lines 
        than create 2 subscription for that sale order
     """,
    'author': 'CLx Media',
    'website': 'https://conversionlogix.com/',
    'category': 'subscription',
    'depends': [
        'clx_budget_management',
        'clx_retail_pricelist',
        'clx_ratio_invoice'

    ],
    'data': [
        'views/sale_order_views.xml',
        'views/sale_subscription_views.xml',
        'wizard/sale_subscription_wizard_views.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
