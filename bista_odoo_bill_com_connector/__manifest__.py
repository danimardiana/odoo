##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2020 (https://www.bistasolutions.com)
#
##############################################################################

{
    'name': "Bista ODOO-Bill.com Connector",
    'version': '0.1',
    'author': 'Bista Solutions Pvt. Ltd.',
    'website': "https://www.bistasolutions.com",
    'category': 'Accounting',
    'depends': ['base', 'account', 'l10n_us', 'contacts', 'payment', 'purchase'],
    'description': """Connector of ODOO and Bill.com""",
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
		'views/res_partner.xml',
		'views/res_partner_bank.xml',
        'views/account_move.xml',
        'views/account_payment_view.xml',
        'views/config_view.xml',
        'wizard/bulk_send_bill_com.xml',
        'views/scheduler.xml',
        'views/journal.xml',
        'views/error_logs.xml',
        'views/account_account.xml',
        ],
    'installable': True,
    'auto_install': False,
}

