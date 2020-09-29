# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
{
    'name': 'CLX Reports',
    'version': '13.3.0.0.11',
    'summary': 'CLX Reports',
    'sequence': 1,
    'description': """ CLX Reports """,
    'category': '',
    'author': 'CLx Media',
    'website': 'https://conversionlogix.com/',
    'depends': ['account',
                'clx_invoice_policy'
                ],
    'data': [
        'views/report_templates.xml',
        'views/report_invoice_document.xml',
        'views/res_company_views.xml'

    ],
    'demo': [
    ],
    'qweb': [

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
