# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

{
    'name': 'CLX Invoice Policy ',
    'version': '13.1.0.1.0',
    'summary': 'CLX Invoice Policy',
    'sequence': 1,
    'description': """CLX Invoice Policy""",
    'category': '',
    'website': '',
    'depends': [
        'sale',
        'sale_subscription',
        'account',
        'clx_subscription_creation',
        'contact_modification',
        'clx_ratio_invoice',
        'analytic',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/schedulers.xml',
        'data/gresystar_sequence.xml',
        'views/clx_invoice_policy_views.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
        'views/product_product_views.xml',
        'views/account_move_email_templates.xml',
        'views/sale_subscription_views.xml',
        'views/invoice_email_template.xml',
        'wizard/generate_invoice_date_range_views.xml',
        'wizard/sale_make_invoice_advance_views.xml',
        'views/account_move_listview_template.xml',
        'views/analytic_account.xml',
        'views/account_asset.xml',
        'views/account_asset_model.xml',
        'views/account_payment_view.xml',
    ],
    'qweb':[
        # 'static/src/xml/account_move_template.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
