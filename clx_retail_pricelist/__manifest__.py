# -*- coding: utf-8 -*-

{
    "name": "CLX Developement",
    'category': 'CLX Developement',
    'summary': 'CLX Developement',
    "author": "CLx Media, Odoo Community Association (OCA)",
    "website": "https://conversionlogix.com/",
    'version': '13.0.0.0.1',
    'sequence': 1,
    'license': 'AGPL-3',
    'description': """""",
    "depends": [
        'sale_management',
        'contact_modification',
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/product_category_view.xml",
        "views/product_pricelist_view.xml",
        "views/sale_order_view.xml",
        "report/sale_report_templates.xml"
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
