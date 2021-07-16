# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

{
    'name': 'CLX Ratio Invoice Creation',
    'category': 'Sale',
    'summary': 'Ration Invoice Creation',
    'author': 'CLx Media',
    'website': 'https://conversionlogix.com/',
    'version': '13.1.0.0.6',
    'sequence': 1,
    'license': 'AGPL-3',
    'description': """Create invoice based on ratio.""",
    'depends': [
                'sale',
                'sale_subscription'
    ],
    'data': [
            # 'security/ir.model.access.csv',
            # 'data/res_partner_data.xml',
            'views/sale_order_views.xml'

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
