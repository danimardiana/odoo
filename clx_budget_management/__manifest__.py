# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

{
    'name': 'Budgets Management',
    'version': '13.3.0.0.17',
    'summary': 'Budgets Management',
    'sequence': 1,
    'description': """ Budgets Management """,
    'category': '',
    'author': 'CLx Media',
    'website': 'https://conversionlogix.com/',
    'depends': [
        'sale_management',
        'sale_subscription',
        'clx_retail_pricelist'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'data/ir_cron.xml',
        'data/mail_template.xml',
        'views/sale_budget_views.xml',
        'views/res_config_settings_views.xml',
        'views/sale_order_views.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
