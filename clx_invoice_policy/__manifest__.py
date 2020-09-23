# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

{
    'name': 'CLX Invoice Policy ',
    'version': '13.1.0.0.7',
    'summary': 'CLX Invoice Policy',
    'sequence': 1,
    'description': """CLX Invoice Policy""",
    'category': '',
    'website': '',
    'depends': [
        'sale',
        'sale_subscription',
        'account',
        'clx_subscription_creation'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/clx_invoice_policy_views.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
        'wizard/sale_advance_payment_inv_views.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
