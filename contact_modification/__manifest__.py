# -*- coding: utf-8 -*-

{
    "name": "Contact Modification",
    'category': 'Contacts',
    'summary': 'To manage Contacts with classification',
    "author": "CLx Media",
    "website": "",
    'version': '13.0.0.0.1',
    'sequence': 1,
    'license': 'AGPL-3',
    'description': """""",
    "depends": [
        'contacts',
        'account',
        'purchase'
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
