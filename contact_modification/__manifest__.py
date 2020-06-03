# -*- coding: utf-8 -*-

{
    "name": "Contact Modification",
    'category': 'Contact Modification',
    'summary': 'Contact Modification',
    "author": "",
    'version': '13.0.0.0.1',
    'description': """
        """,
    "depends": [
        'base','contacts','account','purchase'
    ],
    "data": [
        'security/ir.model.access.csv',
        "data/contact.xml",
        "views/res_partner_view.xml",
        "views/purchase_view.xml",
    ],
   
    'installable': True,
    'application': False,
    'auto_install': False,
}
