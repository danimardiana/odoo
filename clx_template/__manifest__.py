# -*- coding: utf-8 -*-
{
    'name': "CLX Template",
    'author': "Conversion Logix",
    'summary': """
     CLX Template.
        """,

    'description':
    """
	Modyfying the default Odoo template with custom styling.
    """,
    'license': "OPL-1",
    'category': 'Theme/Creative',
    'version': '1.0.0.0.0',
    'price': 0,
    'currency': "EUR",
    'depends': ['website', 'website_theme_install'],
    'images': ['static/src/img/logo.png'],
    'data': [
        'views/assets.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
