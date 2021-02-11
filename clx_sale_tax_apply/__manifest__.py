# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

{
    'name': 'Sale order tax apply',
    'version': '13.1.1.0.2',
    'sequence': 1,
    'description': """ Apply tax only for TCC type category product.
     """,
    'author': 'CLx Media',
    'website': 'https://conversionlogix.com/',
    'category': 'subscription',
    'depends': [
        'account',
        'sale'
    ],
    'data': [
        'views/account_tax_views.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
