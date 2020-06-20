# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
{
    "name": "Contact Modification",
    'category': 'Contacts',
    'summary': 'To manage Contacts with classification',
    "author": "CLx Media, Odoo Community Association (OCA)",
    "website": "https://conversionlogix.com/",
    'version': '13.0.0.0.5',
    'sequence': 1,
    'license': 'AGPL-3',
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
        "views/res_partner_clx_child.xml",
        "views/menu.xml"
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
