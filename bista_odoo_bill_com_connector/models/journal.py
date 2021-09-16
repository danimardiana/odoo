# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class AccountJournal(models.Model):
    _inherit = "account.journal"

    bill_com_journal = fields.Boolean('Bill.com Journal', copy=False, tracking=True)

    def name_get(self):
        result = []
        for rec in self:
            journal_name = rec.name
            currency = rec.currency_id or rec.company_id.currency_id
            name = "%s (%s)" % (journal_name, currency.name)
            bank_account_id = rec.bank_account_id
            if bank_account_id and bank_account_id.acc_number and bank_account_id:
                acc_number = '***'  + str(bank_account_id.acc_number)[-4:]
                result.append((rec.id, "%s - %s" % (name, acc_number)))
            else:
                result.append((rec.id, "%s" % (name)))
        return result