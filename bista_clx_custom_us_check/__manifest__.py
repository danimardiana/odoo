# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
{
    "name": "Custom us check report",
    "version": "13.1.0",
    "summary": "Custom us check report",
    "sequence": 1,
    "description": """ Custom us check report  """,
    "catego": "",
    "author": 'Bista Solutions Pvt. Ltd.',
    "website": "https://www.bistasolutions.com",
    "depends": ["l10n_us_check_printing"],
    "data": [
        'views/print_check.xml'
    ],
    "demo": [],
    "qweb": [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
