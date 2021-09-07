##############################################################################
#
#    Bista Solutions
#    Copyright (C) 2019 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models, _
from .connection import BillComService
from odoo.exceptions import UserError, ValidationError
import json
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime, timedelta


class BillComConfig(models.Model):
    _name = 'bill.com.config'
    _description = 'Bill.com Configuration'

    name = fields.Char('Name')
    bill_com_user_name = fields.Char("Username", copy=False)
    bill_com_password = fields.Char("Password", copy=False)
    bill_com_orgid = fields.Char("Organization ID", copy=False)
    bill_com_devkey = fields.Char("Developer Key", copy=False)
    bill_com_login_url = fields.Char("Login URL", copy=False)
    bill_com_vendor_create_url = fields.Char("Vendor Create URL", copy=False)
    bill_com_vendor_update_url = fields.Char("Vendor Update URL", copy=False)
    bill_com_vendor_bank_account_create_url = fields.Char("Vendor Bank Account Create URL", copy=False)
    bill_com_vendor_bank_account_update_url = fields.Char("Vendor Bank Account Update URL", copy=False)
    bill_com_bill_create_url = fields.Char("Bill Create URL", copy=False)
    bill_com_bill_update_url = fields.Char("Bill Update URL", copy=False)
    bill_com_organization_bank_account_url = fields.Char("Organization Bank Accounts URL", copy=False)
    bill_com_payment_create_url = fields.Char("Payment Create URL:", copy=False)
    bill_com_environment = fields.Selection([('sandbox','Sandbox'), ('production','Production')], string="Environment", copy=False, default='sandbox')
    bill_com_mfa_challenge_create_url = fields.Char("MFA Challenge URL", copy=False)
    bill_com_mfa_challenge_authenticate_url = fields.Char("MFA Authenticate URL", copy=False)
    bill_com_mfa_challenge = fields.Char("MFA Challenge", copy=False)
    bill_com_device_name = fields.Char("Device Name", copy=False)
    bill_com_machine_name = fields.Char("Machine Name", copy=False)
    bill_com_mfa_token = fields.Char("MFA Token", copy=False)
    bill_com_mfa_id = fields.Char("MFA ID", copy=False)
    company_id = fields.Many2one('res.company', 'Company', copy=False)
    bill_com_payment_import_url = fields.Char("Payment Import URL", copy=False)
    bill_com_payment_cancel_url = fields.Char("Payment Cancel URL", copy=False)
    last_payment_imported_date = fields.Datetime('Payment Imported Date', copy=False)
    bill_com_vendor_import_url = fields.Char("Vendor Import URL", copy=False)
    bill_com_vendor_bank_account_import_url = fields.Char("Vendor Bank Accounts Import URL", copy=False)
    bill_com_bill_import_url = fields.Char("Bill Import URL", copy=False)
    last_bill_imported_date = fields.Datetime('Bill Imported Date', copy=False)
    bill_com_bill_status = fields.Selection([('1','Unpaid'),('2','Partially Paid'), ('4','Scheduled'), ('0','Paid'), ('all', 'All')], string="Payment Status", copy=False, default='all')
    bill_com_coa_import_url = fields.Char("Chart of Account Import URL", copy=False)

    def get_bill_com_config(self, company_id):
        bill_com_config_obj = False
        if company_id:
            bill_com_config_obj = self.search([('company_id', '=', company_id)], limit=1)
        return bill_com_config_obj

    @api.constrains('company_id')
    def _check_company_id(self):
        bill_com_config_obj = self.env['bill.com.config']
        for each_config in self.sudo():
            company_id = each_config.company_id
            same_company_id_rec  = bill_com_config_obj.sudo().search([('id', '!=', each_config.id),('company_id', '=', company_id.id)])
            if same_company_id_rec:
                raise ValidationError(_('You cannot have multiple Bill.com Configuration for same company.'))

    @api.onchange('bill_com_environment')
    def onchange_bill_com_environment(self):
        bill_com_environment = self.bill_com_environment
        if bill_com_environment == 'sandbox':
            self.bill_com_login_url = 'https://api-sandbox.bill.com/api/v2/Login.json'
            self.bill_com_vendor_create_url = 'https://api-sandbox.bill.com/api/v2/Crud/Create/Vendor.json'
            self.bill_com_vendor_update_url = 'https://api-sandbox.bill.com/api/v2/Crud/Update/Vendor.json'
            self.bill_com_vendor_bank_account_create_url = 'https://api-sandbox.bill.com/api/v2/Crud/Create/VendorBankAccount.json'
            self.bill_com_vendor_bank_account_update_url = 'https://api-sandbox.bill.com/api/v2/Crud/Delete/VendorBankAccount.json'
            self.bill_com_bill_create_url = 'https://api-sandbox.bill.com/api/v2/Bulk/Crud/Create/Bill'
            self.bill_com_bill_update_url = 'https://api-sandbox.bill.com/api/v2/Bulk/Crud/Update/Bill'
            self.bill_com_mfa_challenge_create_url = 'https://api-sandbox.bill.com/api/v2/MFAChallenge.json'
            self.bill_com_mfa_challenge_authenticate_url = 'https://api-sandbox.bill.com/api/v2/MFAAuthenticate.json'
            self.bill_com_organization_bank_account_url = 'https://api-sandbox.bill.com/api/v2/List/BankAccount.json'
            self.bill_com_payment_create_url = 'https://api-sandbox.bill.com/api/v2/PayBills.json'
            self.bill_com_payment_import_url = 'https://api-sandbox.bill.com/api/v2/List/SentPay.json'
            self.bill_com_payment_cancel_url = 'https://api-sandbox.bill.com/api/v2/CancelAPPayment.json'
            self.bill_com_vendor_import_url = 'https://api-sandbox.bill.com/api/v2/List/Vendor.json'
            self.bill_com_vendor_bank_account_import_url = 'https://api-sandbox.bill.com/api/v2/List/VendorBankAccount.json'
            self.bill_com_bill_import_url = 'https://api-sandbox.bill.com/api/v2/List/Bill.json'
            self.bill_com_coa_import_url = 'https://api-sandbox.bill.com/api/v2/List/ChartOfAccount.json'
        else:
            self.bill_com_login_url = 'https://api.bill.com/api/v2/Login.json'
            self.bill_com_vendor_create_url = 'https://api.bill.com/api/v2/Crud/Create/Vendor.json'
            self.bill_com_vendor_update_url = 'https://api.bill.com/api/v2/Crud/Update/Vendor.json'
            self.bill_com_vendor_bank_account_create_url = 'https://api.bill.com/api/v2/Crud/Create/VendorBankAccount.json'
            self.bill_com_vendor_bank_account_update_url = 'https://api.bill.com/api/v2/Crud/Delete/VendorBankAccount.json'
            self.bill_com_bill_create_url = 'https://api.bill.com/api/v2/Bulk/Crud/Create/Bill'
            self.bill_com_bill_update_url = 'https://api.bill.com/api/v2/Bulk/Crud/Update/Bill'
            self.bill_com_mfa_challenge_create_url = 'https://api.bill.com/api/v2/MFAChallenge.json'
            self.bill_com_mfa_challenge_authenticate_url = 'https://api.bill.com/api/v2/MFAAuthenticate.json'
            self.bill_com_organization_bank_account_url = 'https://api.bill.com/api/v2/List/BankAccount.json'
            self.bill_com_payment_create_url = 'https://api.bill.com/api/v2/PayBills.json'
            self.bill_com_payment_import_url = 'https://api.bill.com/api/v2/List/SentPay.json'
            self.bill_com_payment_cancel_url = 'https://api.bill.com/api/v2/CancelAPPayment.json'
            self.bill_com_vendor_import_url = 'https://api.bill.com/api/v2/List/Vendor.json'
            self.bill_com_vendor_bank_account_import_url = 'https://api.bill.com/api/v2/List/VendorBankAccount.json'
            self.bill_com_bill_import_url = 'https://api.bill.com/api/v2/List/Bill.json'
            self.bill_com_coa_import_url = 'https://api.bill.com/api/v2/List/ChartOfAccount.json'

    def get_organizational_bank_accounts_details(self):
        bill_com_user_name = self.bill_com_user_name
        bill_com_password = self.bill_com_password
        bill_com_orgid = self.bill_com_orgid
        bill_com_devkey = self.bill_com_devkey
        bill_com_login_url = self.bill_com_login_url
        bill_com_organization_bank_account_url = self.bill_com_organization_bank_account_url
        bill_com_service_obj = BillComService(bill_com_user_name, bill_com_password, bill_com_orgid, bill_com_devkey, bill_com_login_url)
        data = '''{"start" : 0, "max" : 999}'''
        bill_com_service_obj.get_organizational_bank_accounts_details(bill_com_organization_bank_account_url, data)

    def get_mfn_challenge(self):
        bill_com_user_name = self.bill_com_user_name
        bill_com_password = self.bill_com_password
        bill_com_orgid = self.bill_com_orgid
        bill_com_devkey = self.bill_com_devkey
        bill_com_login_url = self.bill_com_login_url
        bill_com_mfa_challenge_create_url = self.bill_com_mfa_challenge_create_url
        bill_com_service_obj = BillComService(bill_com_user_name, bill_com_password, bill_com_orgid, bill_com_devkey, bill_com_login_url)
        data = '''{"useBackup" : false}'''
        challengeId = bill_com_service_obj.get_mfn_challenge(bill_com_mfa_challenge_create_url, data)
        if challengeId:
            self.bill_com_mfa_challenge = challengeId

    def mfn_authenticate(self):
        bill_com_mfa_token = self.bill_com_mfa_token
        if not bill_com_mfa_token:
            raise UserError(_("Please Enter MFA Token"))
        bill_com_device_name = self.bill_com_device_name
        if not bill_com_device_name:
            raise UserError(_("Please Enter Device Name"))
        bill_com_machine_name = self.bill_com_machine_name
        if not bill_com_machine_name:
            raise UserError(_("Please Enter Machine Name"))
        bill_com_mfa_challenge = self.bill_com_mfa_challenge
        if not bill_com_mfa_challenge:
            raise UserError(_("Please Enter MFA Challenge"))
        bill_com_user_name = self.bill_com_user_name
        bill_com_password = self.bill_com_password
        bill_com_orgid = self.bill_com_orgid
        bill_com_devkey = self.bill_com_devkey
        bill_com_login_url = self.bill_com_login_url
        bill_com_mfa_challenge_authenticate_url = self.bill_com_mfa_challenge_authenticate_url
        bill_com_service_obj = BillComService(bill_com_user_name, bill_com_password, bill_com_orgid, bill_com_devkey, bill_com_login_url)
        data={"challengeId" : bill_com_mfa_challenge, "token" : bill_com_mfa_token, "deviceId" : bill_com_device_name,
                "machineName" : bill_com_machine_name,"rememberMe" : 'true'}
        data = json.dumps(data)
        mfaId = bill_com_service_obj.mfn_authenticate(bill_com_mfa_challenge_authenticate_url, data)
        if mfaId:
            self.bill_com_mfa_id = mfaId        

    @api.model
    def auto_bill_com_payment_import(self, from_date='', to_date='', bill_payment_id=''):
        context = self._context.copy()
        if from_date and to_date:
            context.update({'from_date': from_date, 'to_date': to_date})
        if bill_payment_id:
            context.update({'bill_payment_id': bill_payment_id})
        context.update({'from_scheduler': True})
        search_config = self.env['bill.com.config'].search([])
        search_config.with_context(context).import_bill_com_payments()

    @api.model
    def auto_bill_com_bill_import(self, from_date='', to_date='', bill_id=''):
        context = self._context.copy()
        if from_date and to_date:
            context.update({'from_date': from_date, 'to_date': to_date})
        if bill_id:
            context.update({'bill_id': bill_id})
        context.update({'from_scheduler': True})
        search_config = self.env['bill.com.config'].search([])
        search_config.with_context(context).import_bill_com_bills()
            
    def import_bill_com_payments(self):
        context = self._context
        for each_config in self:
            last_payment_imported_date = each_config.last_payment_imported_date
            if not last_payment_imported_date and not 'from_scheduler' in context:
                raise UserError(_("Please Enter Last Imported Date"))
            company_id = each_config.company_id
            bill_com_user_name = each_config.bill_com_user_name
            bill_com_password = each_config.bill_com_password
            bill_com_orgid = each_config.bill_com_orgid
            bill_com_devkey = each_config.bill_com_devkey
            bill_com_login_url = each_config.bill_com_login_url
            bill_com_payment_import_url = each_config.bill_com_payment_import_url
            filter_data = ''
            if 'bill_payment_id' in context:
                bill_payment_id = context.get('bill_payment_id', '')
                filter_data = { "start" : 0, "max" : 999, "filters" : [{"field":"id", "op":"=", "value": bill_payment_id}]}
            elif 'from_date' in context and 'to_date' in context:
                from_date = context.get('from_date', '')
                to_date = context.get('to_date', '')
                filter_data = { "start" : 0, "max" : 999, "filters" : [{"field":"updatedTime", "op":">=", "value": from_date}, {"field":"updatedTime", "op":"<=", "value": to_date}]}
            elif last_payment_imported_date:
                last_payment_imported_date = fields.Date.to_string(last_payment_imported_date - timedelta(1))
                filter_data = { "start" : 0, "max" : 999, "filters" : [{"field":"updatedTime", "op":">", "value": last_payment_imported_date}]}
            if filter_data: 
                bill_com_service_obj = BillComService(bill_com_user_name, bill_com_password, bill_com_orgid, bill_com_devkey, bill_com_login_url)   
                filter_data = json.dumps(filter_data)
                payment_data = bill_com_service_obj.import_bill_payments(bill_com_payment_import_url, filter_data)
                if payment_data:
                    cr = self._cr
                    payment_obj = self.env['account.payment']
                    account_move_obj = self.env['account.move']
                    for each_data in payment_data:
                        status = each_data.get('status', '')
                        bill_com_payment_id = each_data.get('id', '')
                        amount = each_data.get('amount', 0.0)
                        processDate = each_data.get('processDate', '')
                        bankAccountId = each_data.get('bankAccountId', '')
                        if status in ('1', '2', '3','4') and bankAccountId:
                            cr.execute("select id, state from account_payment where bill_com_payment_id='%s'" % (bill_com_payment_id))
                            odoo_payment_ids = list(filter(None, map(lambda x: x, cr.fetchall())))
                            if odoo_payment_ids:
                                for each_odoo_payment_id in odoo_payment_ids:
                                    payment_id = each_odoo_payment_id[0]
                                    payment_id_state = each_odoo_payment_id[1]
                                    payment_id_brw = payment_obj.sudo().browse(payment_id)
                                    if status in ('1', '2') :
                                        if status == '1':
                                            payment_id_brw.bill_com_payment_status = 'Scheduled'
                                        elif status == '2':
                                            payment_id_brw.bill_com_payment_status = 'Paid'    
                                    elif status in ('3', '4') and payment_id_state != 'cancelled':
                                        payment_id_brw.with_context({'from_bill_com_cancel': True}).action_draft()
                                        payment_id_brw.cancel()
                                        payment_id_brw.bill_com_payment_status = 'Cancelled'
                            else:    
                                billPays = each_data.get('billPays', [])
                                billIds = []
                                for each_bill_data in billPays:
                                    billId = each_bill_data.get('billId')
                                    amount = each_bill_data.get('amount')
                                    bill_name = each_bill_data.get('name')
                                    billIds.append(billId)
                                    cr.execute("""select id from account_move where bill_com_bill_id = '%s'""" % (billId))
                                    odoo_invoice_ids = list(filter(None, map(lambda x: x[0], cr.fetchall())))
                                    if odoo_invoice_ids and status in ('1', '2'):
                                        odoo_invoice_id_brw = account_move_obj.browse(odoo_invoice_ids[0])
                                        company_id = odoo_invoice_id_brw.company_id.id
                                        cr.execute("""select journal.id from account_journal journal
                                                    inner join res_partner_bank bank_acc on bank_acc.id = journal.bank_account_id
                                                    where (bank_acc.acc_number = '%s' or  bank_acc.bill_com_organization_bank_account_id = '%s') and journal.company_id = %s""" % (bankAccountId, bankAccountId, company_id))
                                        journal_id = list(filter(None, map(lambda x: x[0], cr.fetchall())))
                                        if journal_id:
                                            payment_vals = {'amount': amount, 'bill_com_payment_id': bill_com_payment_id, 'payment_date': processDate,
                                                'journal_id': journal_id[0], 'payment_type': 'outbound', 'partner_type': 'supplier', 'company_id': company_id,
                                                'invoice_ids': [(6, 0, odoo_invoice_ids)],
                                                'partner_id': odoo_invoice_id_brw.commercial_partner_id.id,
                                                'communication': odoo_invoice_id_brw.name,
                                                'payment_method_id': 1}
                                            new_payment_id = payment_obj.create(payment_vals)
                                            new_payment_id.post()
                                            if status == '1':
                                                new_payment_id.bill_com_payment_status = 'Scheduled'
                                            elif status == '2':
                                                new_payment_id.bill_com_payment_status = 'Paid'
            current_date_time = fields.Datetime.now()                        
            each_config.last_payment_imported_date = current_date_time

    def check_duplicate_vendor_reference(self, ref, partner_id, invoice_date):
        cr = self._cr
        cr.execute("""SELECT id from account_move move where move.ref='%s' and move.partner_id=%s and (move.invoice_date is Null or move.invoice_date='%s')""" % (ref, partner_id, invoice_date))
        invoice_exists = list(filter(None, map(lambda x: x, cr.fetchall())))
        if invoice_exists:
            return True
        return False

    
    def get_line_account(self, bill_com_coa_id, product_id, journal_id, company_id):
        account_id = False
        search_odoo_account_id = self.env['account.account'].search([('bill_com_coa_id', '=', bill_com_coa_id), ('company_id', '=', company_id)], limit=1)
        if search_odoo_account_id:
            return search_odoo_account_id.id
        if product_id:    
            accounts = product_id.product_tmpl_id.get_product_accounts(fiscal_pos=False)
            if accounts and accounts.get('income'):
                account_id = accounts.get('income', False)
        elif journal_id:
            account_id = journal_id.default_credit_account_id
        return account_id    
            
        

    def import_bill_com_bills(self):
        context = self._context.copy()
        for each_config in self:
            last_bill_imported_date = each_config.last_bill_imported_date
            if not last_bill_imported_date and not 'from_scheduler' in context:
                raise UserError(_("Please Enter Last Imported Date"))
            bill_com_user_name = each_config.bill_com_user_name
            bill_com_password = each_config.bill_com_password
            bill_com_orgid = each_config.bill_com_orgid
            bill_com_devkey = each_config.bill_com_devkey
            bill_com_login_url = each_config.bill_com_login_url
            bill_com_bill_import_url = each_config.bill_com_bill_import_url
            bill_com_bill_status =  each_config.bill_com_bill_status
            bill_com_vendor_import_url = each_config.bill_com_vendor_import_url
            company_id = each_config.company_id
            filter_data = ''
            if 'bill_id' in context:
                bill_id = context.get('bill_id', '')
                filter_data = {"start": 0, "max": 999,
                               "filters": [{"field": "id", "op": "=", "value": bill_id},
                               {"field": "isActive", "op": "=", "value": "1"}]}
            elif 'from_date' in context and 'to_date' in context:
                from_date = context.get('from_date', '')
                to_date = context.get('to_date', '')
                filter_data = {"start": 0, "max": 999,
                               "filters": [{"field": "updatedTime", "op": ">=", "value": from_date},
                                           {"field": "updatedTime", "op": "<=", "value": to_date},
                                           {"field": "isActive", "op": "=", "value": "1"}
                                           ]}
                if bill_com_bill_status and bill_com_bill_status != 'all':
                    filter_data["filters"].append({"field": "paymentStatus", "op": "=", "value": bill_com_bill_status})
            elif last_bill_imported_date:
                # last_bill_imported_date = fields.Date.to_string(last_bill_imported_date - timedelta(1))
                last_bill_imported_date = fields.Date.to_string(last_bill_imported_date)
                filter_data = {"start": 0, "max": 999,
                               "filters": [{"field": "updatedTime", "op": ">", "value": last_bill_imported_date},
                                            {"field": "isActive", "op": "=", "value": "1"}]}
                if bill_com_bill_status and bill_com_bill_status != 'all':
                    filter_data["filters"].append({"field": "paymentStatus", "op": "=", "value": bill_com_bill_status})                                
            if filter_data:
                bill_com_service_obj = BillComService(bill_com_user_name, bill_com_password, bill_com_orgid,
                                                      bill_com_devkey, bill_com_login_url)
                filter_data = json.dumps(filter_data)
                bill_data = bill_com_service_obj.import_bills(bill_com_bill_import_url, filter_data)
                cr = self._cr
                account_move_obj = self.env['account.move']
                purchase_order_obj = self.env['purchase.order']
                partner_obj = self.env['res.partner']
                error_logs_obj = self.env['bill.com.error.logs']
                product_obj = self.env['product.product']
                journal_obj = self.env['account.journal']
                if bill_data:
                    for each_data in bill_data:
                        try:
                            bill_com_bill_id = each_data.get('id', '')
                            bill_com_vendor_id = each_data.get('vendorId', '')
                            invoice_number = each_data.get('invoiceNumber', '')
                            po_number = each_data.get('poNumber', '')
                            bill_amount = each_data.get('amount')
                            invoiceDate = each_data.get('invoiceDate')
                            dueDate = each_data.get('dueDate')
                            reference = invoice_number
                            cr.execute("select id from res_partner where bill_com_vendor_id='%s'" %(bill_com_vendor_id))
                            odoo_vendor_id = list(filter(None, map(lambda x: x[0], cr.fetchall())))
                            if not odoo_vendor_id:
                                filter_data = {"start" : 0, "max" : 999,"filters": [{"field": "id", "op": "=", "value": bill_com_vendor_id}]} 
                                filter_data = json.dumps(filter_data)
                                response_vendor_data = bill_com_service_obj.import_vendor_data(bill_com_vendor_import_url, filter_data)
                                if response_vendor_data:
                                    response_vendor_data =  response_vendor_data[0]
                                    vendor_name = response_vendor_data.get('name', '')
                                    isActive = response_vendor_data.get('isActive', '')
                                    address1 = response_vendor_data.get('address1', '')
                                    address2 = response_vendor_data.get('address2', '')
                                    addressCity = response_vendor_data.get('addressCity', '')
                                    addressZip = response_vendor_data.get('addressZip', '')
                                    addressCity = response_vendor_data.get('addressCity', '')
                                    addressCountry = response_vendor_data.get('addressCountry','')
                                    odoo_country_rec_id = odoo_state_rec_id = False
                                    if addressCountry:
                                        cr.execute("select id from res_country where name ilike '%s'" % (addressCountry))
                                        odoo_country_id = list(filter(None, map(lambda x: x[0], cr.fetchall())))
                                        if odoo_country_id:
                                            odoo_country_rec_id = odoo_country_id[0]
                                            addressState = response_vendor_data.get('addressState')
                                            if addressState:
                                                cr.execute("select id from res_country_state where code='%s' and country_id=%s" % (addressState, odoo_country_id[0]))
                                                odoo_state_id = list(filter(None, map(lambda x: x[0], cr.fetchall())))
                                                if odoo_state_id:
                                                    odoo_state_rec_id = odoo_state_id[0]
                                    phone = response_vendor_data.get('phone', '')
                                    email = response_vendor_data.get('email', '')
                                    vals = {'supplier_rank': 1,'name': vendor_name, 'bill_com_vendor_id': bill_com_vendor_id, 'email': email if email else False,
                                    'active': True if isActive== '1' else False, 'street': address1, 'street2': address2, 'city':addressCity,
                                    'zip': addressZip, 'country_id': odoo_country_rec_id, 'state_id': odoo_state_rec_id, 'phone': phone if phone else ''}
                                    odoo_vendor_id = [partner_obj.create(vals).id]
                            if odoo_vendor_id:
                                journal_id = journal_obj.search([('company_id', '=', company_id.id), ('type', '=', 'purchase')], limit=1)
                                cr.execute("select id from account_move where bill_com_bill_id='%s' and type='in_invoice'" % (bill_com_bill_id))
                                odoo_bill_id = list(filter(None, map(lambda x: x[0], cr.fetchall())))
                                cr.execute("select id from purchase_order where partner_ref='%s'" % (reference))
                                odoo_purchase_order_id = list(filter(None, map(lambda x: x[0], cr.fetchall())))
                                billLineItems = each_data.get('billLineItems', [])
                                line_vals = []
                                for each_line_data in billLineItems:
                                    description = each_line_data.get('description', '')
                                    chartOfAccountId = each_line_data.get('chartOfAccountId', '')
                                    description_brw = description.find('[') if description else ''
                                    purchase_line_id = False
                                    if description_brw == 0:
                                        odoo_internal_reference = description.split('[', 1)[1].split(']')[0]
                                        product_id = product_obj.search(['|',('default_code', '=', odoo_internal_reference), ('name', '=', description)], limit=1)
                                    else:
                                        product_id = product_obj.search([('name', '=', description)], limit=1)
                                    quantity = each_line_data.get('quantity', 1)
                                    subtotal = each_line_data.get('amount', 0.0)
                                    unit_price = each_line_data.get('unit_price', 0.0)
                                    if not quantity:
                                        quantity = 1
                                    if 'quantity' not in each_line_data:
                                        quantity = subtotal / unit_price   
                                    if 'unit_price' in each_line_data:
                                        unit_price = unit_price
                                    else:        
                                        unit_price =  subtotal / quantity
                                    if odoo_purchase_order_id and product_id:
                                        cr.execute("select id from purchase_order_line where order_id=%s and product_id=%s" % (odoo_purchase_order_id[0], product_id.id))
                                        purchase_line_id = list(filter(None, map(lambda x: x[0], cr.fetchall())))
                                    line_account_id = self.get_line_account(chartOfAccountId, product_id if product_id else False, journal_id, company_id.id)
                                    line_vals.append((0, 0, {
                                            'name': description, 'product_id': product_id.id if product_id else False, 'quantity': quantity,
                                            'price_unit': unit_price, 'price_subtotal': unit_price,
                                            'purchase_line_id': purchase_line_id[0] if purchase_line_id else False,
                                            'account_id': line_account_id
                                        }))
                                if odoo_bill_id:
                                    existing_bill_id = account_move_obj.sudo().browse(odoo_bill_id[0])
                                    invoice_payments_widget = existing_bill_id.invoice_payments_widget
                                    if invoice_payments_widget == 'false':
                                        bill_vals = {
                                                       'bill_com_bill_id': bill_com_bill_id,
                                                       'partner_id': odoo_vendor_id[0],
                                                       'invoice_line_ids': line_vals, 'type': 'in_invoice',
                                                       'invoice_date': invoiceDate, 'invoice_date_due': dueDate,
                                                       'invoice_origin': po_number,
                                                       'journal_id': journal_id.id if journal_id else False,
                                                       'company_id': company_id.id
                                                        }
                                        existing_ref = existing_bill_id.ref
                                        if existing_ref != invoice_number:
                                            if not self.check_duplicate_vendor_reference(invoice_number, odoo_vendor_id[0], invoiceDate):
                                                bill_vals.update({'ref': invoice_number})
                                            else:
                                                error_message = "%s(%s) - Duplicate Reference Number exists for the same vendor" % (invoice_number, bill_com_bill_id)
                                                error_logs_obj.create_error_log('Import Bill', str(error_message))
                                                continue
                                        existing_bill_id.invoice_line_ids = False
                                        existing_bill_id.write(bill_vals)
                                    else:
                                        odoo_bill_amount = existing_bill_id.amount_total
                                        if odoo_bill_amount != bill_amount:
                                            error_message = "%s(%s) - Total Mismatch occured due to Edit of Bill in Bill.com after releasing some payment.\n ODOO Total: %s and Bill.com Total: %s" % (invoice_number, bill_com_bill_id, odoo_bill_amount, bill_amount)
                                            error_logs_obj.create_error_log('Import Bill', str(error_message))
                                    odoo_bill_id = odoo_bill_id[0]        
                                elif line_vals:
                                    if not self.check_duplicate_vendor_reference(invoice_number, odoo_vendor_id[0], invoiceDate):
                                        bill_vals = {
                                                     'partner_id': odoo_vendor_id[0], 'ref': invoice_number,'bill_com_bill_id': bill_com_bill_id,
                                                     'invoice_line_ids': line_vals, 'type': 'in_invoice', 'invoice_date': invoiceDate, 'invoice_date_due': dueDate, 'state': 'draft',
                                                     'invoice_origin': po_number,
                                                     'journal_id': journal_id.id if journal_id else False,
                                                     'company_id': company_id.id}
                                        odoo_bill_id = account_move_obj.create(bill_vals)
                                        odoo_bill_id.with_context({'from_import_bill': True}).action_post()
                                        odoo_bill_id = odoo_bill_id.id
                                    else:
                                        error_message = "%s(%s) - Duplicate Reference Number exists for the same vendor." % (invoice_number, bill_com_bill_id)
                                        error_logs_obj.create_error_log('Import Bill', str(error_message))
                                if odoo_bill_id:
                                    cr.execute("select purchase_order_id from account_move_purchase_order_rel where account_move_id='%s'" % (odoo_bill_id))
                                    purchase_order_id = list(filter(None, map(lambda x: x[0], cr.fetchall())))
                                    if purchase_order_id:
                                        purchase_order_obj.browse(purchase_order_id[0])._compute_invoice()
                                    if odoo_purchase_order_id:
                                        purchase_order_obj.browse(odoo_purchase_order_id[0])._compute_invoice()
                        except Exception as e:
                            error_message = "%s(%s) - %s" % (invoice_number, bill_com_bill_id, str(e))
                            error_logs_obj.create_error_log('Import Bill', str(error_message))
            current_date_time = fields.Datetime.now()
            each_config.last_bill_imported_date = current_date_time

    def import_vendor_data(self):
        context = self._context
        for each_config in self:
            bill_com_vendor_import_url = each_config.bill_com_vendor_import_url
            if not bill_com_vendor_import_url:
                raise ValidationError(_('Missing Vendor Import URL !'))
            company_id = each_config.company_id
            bill_com_user_name = each_config.bill_com_user_name
            bill_com_password = each_config.bill_com_password
            bill_com_orgid = each_config.bill_com_orgid
            bill_com_devkey = each_config.bill_com_devkey
            bill_com_login_url = each_config.bill_com_login_url
            vendor_data, final_vendor_data = True, []
            start = 0
            max_range = 999
            while vendor_data:
                filter_data = {"start" : start, "max" : max_range}
                bill_com_service_obj = BillComService(bill_com_user_name, bill_com_password, bill_com_orgid, bill_com_devkey, bill_com_login_url)   
                filter_data = json.dumps(filter_data)
                response_vendor_data = bill_com_service_obj.import_vendor_data(bill_com_vendor_import_url, filter_data)
                if response_vendor_data:
                    final_vendor_data = final_vendor_data + response_vendor_data
                    start = start + max_range
                else:
                    vendor_data = False
            cr = each_config._cr
            partner_obj = self.env['res.partner']
            i = 1
            _logger.info('length of Vendor Data %s', len(final_vendor_data))
            for each_vendor_data in final_vendor_data:
                _logger.info('i value %s', i)
                vendor_id = each_vendor_data.get('id')
                if vendor_id:
                    query_string = "supplier_rank > 0 and (bill_com_vendor_id='%s'"%(vendor_id)
                    name = each_vendor_data.get('name')
                    if name == "'\'":
                        continue
                    name = name.replace("'", "''")
                    query_string += " or name ilike '%s')"%(name)
                    email = each_vendor_data.get('email')
                    #if email:
                     #   query_string += " or email='%s'"%(email)
                    cr.execute("select id from res_partner where %s limit 1" % (query_string))
                    odoo_vendor_id = list(filter(None, map(lambda x: x[0], cr.fetchall())))
                    _logger.info('odoo_vendor_id %s, %s', odoo_vendor_id, query_string)
                    isActive = each_vendor_data.get('isActive')
                    address1 = each_vendor_data.get('address1')
                    address2 = each_vendor_data.get('address2')
                    addressCity = each_vendor_data.get('addressCity')
                    addressZip = each_vendor_data.get('addressZip')
                    addressCity = each_vendor_data.get('addressCity')
                    addressCountry = each_vendor_data.get('addressCountry')
                    odoo_country_rec_id = odoo_state_rec_id = False
                    if addressCountry:
                        cr.execute("select id from res_country where name ilike '%s'" % (addressCountry))
                        odoo_country_id = list(filter(None, map(lambda x: x[0], cr.fetchall())))
                        if odoo_country_id:
                            odoo_country_rec_id = odoo_country_id[0]
                            addressState = each_vendor_data.get('addressState')
                            if addressState:
                                cr.execute("select id from res_country_state where code='%s' and country_id=%s" % (addressState, odoo_country_id[0]))
                                odoo_state_id = list(filter(None, map(lambda x: x[0], cr.fetchall())))
                                if odoo_state_id:
                                    odoo_state_rec_id = odoo_state_id[0]
                    phone = each_vendor_data.get('phone')
                    vals = {'supplier_rank': 1,'name': name, 'bill_com_vendor_id': vendor_id, 'email': email if email else False,
                    'active': True if isActive== '1' else False, 'street': address1, 'street2': address2, 'city':addressCity,
                    'zip': addressZip, 'country_id': odoo_country_rec_id, 'state_id': odoo_state_rec_id, 'phone': phone if phone else ''}
                    if not odoo_vendor_id:
                        partner_obj.create(vals)
                    else:
                        partner_id_brw = partner_obj.sudo().browse(odoo_vendor_id[0])
                        partner_id_brw.write(vals)
                i = i + 1

    @api.model
    def auto_bill_com_vendor_sync(self):
        search_config = self.env['bill.com.config'].search([])
        search_config.import_vendor_data()

    def import_vendor_bank_account_data(self):
        context = self._context
        for each_config in self:
            bill_com_vendor_bank_account_import_url = each_config.bill_com_vendor_bank_account_import_url
            if not bill_com_vendor_bank_account_import_url:
                raise ValidationError(_('Missing Vendor Bank Accounts Import URL !'))
            company_id = each_config.company_id.id
            bill_com_user_name = each_config.bill_com_user_name
            bill_com_password = each_config.bill_com_password
            bill_com_orgid = each_config.bill_com_orgid
            bill_com_devkey = each_config.bill_com_devkey
            bill_com_login_url = each_config.bill_com_login_url
            vendor_bank_data, final_vendor_bank_data = True, []
            start = 0
            max_range = 999
            while vendor_bank_data:
                filter_data = {"start" : start, "max" : max_range, "filters" : [{"field":"status", "op":"=", "value": '1'}]}
                bill_com_service_obj = BillComService(bill_com_user_name, bill_com_password, bill_com_orgid, bill_com_devkey, bill_com_login_url)   
                filter_data = json.dumps(filter_data)
                response_vendor_bank_data = bill_com_service_obj.import_vendor_bank_account_data(bill_com_vendor_bank_account_import_url, filter_data)
                if response_vendor_bank_data:
                    final_vendor_bank_data = final_vendor_bank_data + response_vendor_bank_data
                    start = start + max_range
                else:
                    vendor_bank_data = False
            cr = each_config._cr
            partner_bank_obj = self.env['res.partner.bank']
            i = 1
            for each_vendor_bank_data in final_vendor_bank_data:
                _logger.info('i value %s', i)
                vendorId = each_vendor_bank_data.get('vendorId')
                _logger.info('vendorId %s', vendorId)
                if vendorId:
                    query_string = "bill_com_vendor_id='%s'"%(vendorId)
                    cr.execute("select id,name from res_partner where bill_com_vendor_id='%s'" % (vendorId))
                    odoo_vendor_data = list(filter(None, map(lambda x: x, cr.fetchall())))
                    if odoo_vendor_data:
                        odoo_vendor_id = odoo_vendor_data[0][0]
                        odoo_vendor_name = odoo_vendor_data[0][1]
                        query_string = ''
                        accountNumber = each_vendor_bank_data.get('accountNumber')[-4:]
                        routingNumber = each_vendor_bank_data.get('routingNumber')
                        bank_bill_id = each_vendor_bank_data.get('id')
                        nameOnAcct = each_vendor_bank_data.get('nameOnAcct')
                        if not nameOnAcct:
                            nameOnAcct = odoo_vendor_name
                        if bank_bill_id and accountNumber and routingNumber:
                            query_string = "(bill_com_vendor_bank_account_id='%s') or (aba_routing='%s' and acc_number ilike '%s') and partner_id=%s"%(bank_bill_id, routingNumber, '%s'%('%'+ accountNumber), odoo_vendor_id)
                            cr.execute("select id from res_partner_bank where %s" % (query_string))
                            odoo_vendor_bank_id_id = list(filter(None, map(lambda x: x[0], cr.fetchall())))
                            _logger.info('odoo_vendor_bank_id_id %s', odoo_vendor_bank_id_id)
                            try:
                                if not odoo_vendor_bank_id_id:
                                    search_bank_acc_id = partner_bank_obj.sudo().search([('acc_number','=', accountNumber), ('company_id','=', company_id)])
                                    if not search_bank_acc_id:
                                        partner_bank_obj.with_context({'default_partner_id': True}).create({'bill_com_vendor_bank_account_id': bank_bill_id, 'aba_routing': routingNumber,
                                       'acc_number': accountNumber, 'active': True, 'partner_id': odoo_vendor_id,
                                       'bank_id': False, 'acc_holder_name': nameOnAcct,
                                       'company_id': company_id
                                       })
                            except Exception as e:
                                pass
                i = i + 1

    def import_bill_com_coa(self):
        context = self._context
        for each_config in self:
            company_id = each_config.company_id.id
            bill_com_user_name = each_config.bill_com_user_name
            bill_com_password = each_config.bill_com_password
            bill_com_orgid = each_config.bill_com_orgid
            bill_com_devkey = each_config.bill_com_devkey
            bill_com_login_url = each_config.bill_com_login_url
            bill_com_coa_import_url = each_config.bill_com_coa_import_url
            filter_data = {"start" : 0,"max" : 999}
            bill_com_service_obj = BillComService(bill_com_user_name, bill_com_password, bill_com_orgid, bill_com_devkey, bill_com_login_url)   
            filter_data = json.dumps(filter_data)
            response_data = bill_com_service_obj.import_coa_api(bill_com_coa_import_url, filter_data)
            if response_data:
                account_account_obj = self.env['account.account']
                for each_response in response_data:
                    accountNumber = each_response.get('accountNumber', '')
                    bill_com_coa_id = each_response.get('id', '')
                    search_odoo_account_id = account_account_obj.search([('code', '=', accountNumber), ('company_id', '=', company_id)], limit=1)
                    if search_odoo_account_id:
                        search_odoo_account_id.write({'bill_com_coa_id': bill_com_coa_id})
                