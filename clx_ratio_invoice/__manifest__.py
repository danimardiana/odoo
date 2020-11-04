# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

{
    'name': 'CLX Ratio Invoice Creation',
    'category': 'Sale',
    'summary': 'Ration Invoice Creation',
    'author': 'CLx Media',
    'website': 'https://conversionlogix.com/',
    'version': '13.1.0.0.2',
    'sequence': 1,
    'license': 'AGPL-3',
    'description': """Create invoice based on ratio.""",
    'depends': [
                'sale',
                'clx_invoice_policy'
    ],
    'data': [
            'security/ir.model.access.csv',
            'data/res_partner_data.xml',
            'views/sale_order_views.xml'

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
