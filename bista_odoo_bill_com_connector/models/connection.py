# -*- coding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2020 (http://www.bistasolutions.com)
#
##############################################################################


from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import json
import logging
_logger = logging.getLogger(__name__)


class BillComService:

    def __init__(self, username, password, orgId, devKey, bill_com_login_url, mfaId=False, deviceId=False):
        self.username = username
        self.password = password
        self.orgId = orgId
        self.devKey = devKey
        data = {'userName': username, 'password': password, 'orgId': orgId,'devKey': devKey}
        if mfaId and deviceId:
            data.update({'mfaId' : mfaId, 'deviceId' : deviceId})
        x = requests.post(bill_com_login_url, data=data)
        response = json.loads(x.text)
        _logger.info('response %s', response)
        if response and response.get('response_message') == 'Success':
            response_data = response.get('response_data',{})
            session_id = response_data.get('sessionId')
            usersId = response_data.get('usersId')
            self.session_id = session_id
            self.usersId = usersId
        elif response and response.get('response_message') == 'Error':
            error_message = response.get('response_data',{}).get('error_message')
            raise UserError(_("%s") % (error_message))

    def get_mfn_challenge(self, mfa_challenge_create_url, challenge_data):
        session_id = self.session_id
        devKey = self.devKey
        challenge_data = str(challenge_data)
        data = {'sessionId': session_id,'devKey': devKey, 'data': '''%s''' %(challenge_data)}
        x = requests.post(mfa_challenge_create_url, headers={"content-type":"application/x-www-form-urlencoded"}, data=data)
        response = json.loads(x.text)
        _logger.info('data %s', data)
        _logger.info('response %s', response)
        if response and response.get('response_message') == 'Success':
            response_data = response.get('response_data',{})
            challengeId =  response_data.get('challengeId')
            return challengeId
        elif response and response.get('response_message') == 'Error':
            error_message = response.get('response_data',{}).get('error_message')
            raise UserError(_("%s") % (error_message))    

    def mfn_authenticate(self, mfa_challenge_authenticate_url, authenticate_data):
        session_id = self.session_id
        devKey = self.devKey
        authenticate_data = str(authenticate_data)
        data = {'sessionId': session_id,'devKey': devKey, 'data': authenticate_data.replace("\'",'').replace('"true"',"true")}
        _logger.info('data %s', data)
        x = requests.post(mfa_challenge_authenticate_url, headers={"content-type":"application/x-www-form-urlencoded"}, data=data)
        response = json.loads(x.text)
        _logger.info('response %s', response)
        if response and response.get('response_message') == 'Success':
            response_data = response.get('response_data',{})
            mfaId =  response_data.get('mfaId')
            return mfaId
        elif response and response.get('response_message') == 'Error':
            error_message = response.get('response_data',{}).get('error_message')
            raise UserError(_("%s") % (error_message))

    def get_organizational_bank_accounts_details(self, bill_com_organization_bank_account_url, data):
        session_id = self.session_id
        devKey = self.devKey
        data = str(data)
        data = {'sessionId': session_id,'devKey': devKey, 'data': '''%s''' %(data)}
        x = requests.post(bill_com_organization_bank_account_url, headers={"content-type":"application/x-www-form-urlencoded"}, data=data)
        response = json.loads(x.text)
        _logger.info('response %s', response)
        if response and response.get('response_message') == 'Success':
            response_data = response.get('response_data', [])
            message = 'Active accounts are as follows: \n\n' 
            message += 'Account Holder Name - Bank Name - Account Number - Routing Number (Bill ID) \n\n'
            for each in response_data:
                isActive = each.get('isActive')
                if isActive == '1':
                    nameOnAcct = each.get('nameOnAcct')
                    bankName = each.get('bankName')
                    accountNumber = each.get('accountNumber')
                    routingNumber = each.get('routingNumber')
                    bankID = each.get('id')
                    message += '%s - %s - %s - %s (%s) \n' % (nameOnAcct, bankName, accountNumber, routingNumber, bankID)
            raise UserError(_("%s") % (message)) 
        elif response and response.get('response_message') == 'Error':
            error_message = response.get('response_data',{}).get('error_message')
            raise UserError(_("%s") % (error_message))

    def create_vendor_api(self, bill_com_vendor_url, vendor_data):
        session_id = self.session_id
        devKey = self.devKey
        vendor_data = str(vendor_data)
        data = {'sessionId': session_id,'devKey': devKey, 'data': '''%s''' %(vendor_data)}
        x = requests.post(bill_com_vendor_url, headers={"content-type":"application/x-www-form-urlencoded"}, data=data)
        response = json.loads(x.text)
        if response and response.get('response_message') == 'Success':
            bill_com_vendor_id =  response.get('response_data',{}).get('id')
            return bill_com_vendor_id
        elif response and response.get('response_message') == 'Error':
            error_message = response.get('response_data',{}).get('error_message')
            raise UserError(_("%s") % (error_message))
        

    def create_update_vendor_bank_account_api(self, bill_com_vendor_bank_account_url, vendor_account_data):
        session_id = self.session_id
        devKey = self.devKey
        vendor_account_data = str(vendor_account_data)
        data = {'sessionId': session_id,'devKey': devKey, 'data': vendor_account_data.replace("\'",'')}
        x = requests.post(bill_com_vendor_bank_account_url, headers={"content-type":"application/x-www-form-urlencoded"}, data=data)
        response = json.loads(x.text)
        _logger.info('response %s', response)
        if response and response.get('response_message') == 'Success':
            response_data = response.get('response_data',{})
            bill_com_vendor_bank_account_id =  response.get('response_data',{}).get('id')
            return bill_com_vendor_bank_account_id
        elif response and response.get('response_message') == 'Error':
            error_message = response.get('response_data',{}).get('error_message')
            raise UserError(_("%s") % (error_message))

    def create_update_bill_api(self, bill_com_bill_url, bill_data):
        session_id = self.session_id
        devKey = self.devKey
        bill_data = str(bill_data)
        data = {'sessionId': session_id,'devKey': devKey, 'data': bill_data.replace("\'",'')}
        x = requests.post(bill_com_bill_url, headers={"content-type":"application/x-www-form-urlencoded"}, data=data)
        response = json.loads(x.text)
        _logger.info('response %s', response)
        bill_com_invoice_data = {}
        if response and response.get('response_message') == 'Success':
            response_data = response.get('response_data',{})
            bulk_data = response_data.get('bulk',{})
            for each_bill_data in bulk_data:
                if each_bill_data.get('response_message') == 'Success':
                    response_data = each_bill_data.get('response_data',{})
                    invoiceNumber = response_data.get('invoiceNumber')
                    bill_com_bill_id = response_data.get('id')
                    bill_com_invoice_data[invoiceNumber] = bill_com_bill_id
            return bill_com_invoice_data      
        elif response and response.get('response_message') == 'Error':
            error_message = response.get('response_data',{}).get('bulk')[0].get('response_data', {}).get('error_message', '')
            raise UserError(_("%s") % (error_message))

    def create_bill_payment_api(self, bill_com_bill_payment_url, payment_data):
        session_id = self.session_id
        devKey = self.devKey
        payment_data = str(payment_data)
        data = { 'sessionId': session_id,'devKey': devKey,  'data': payment_data.replace("\'",'')}
        x = requests.post(bill_com_bill_payment_url, headers={"content-type":"application/x-www-form-urlencoded"}, data=data)
        response = json.loads(x.text)
        _logger.info('response %s', response)
        if response and response.get('response_message') == 'Success':
            response_data = response.get('response_data',{})
            if 'sentPays' in response_data:
                sent_pay_data = response_data.get('sentPays',[])[0]
                bill_com_payment_id = sent_pay_data.get('id')
                bill_com_payment_status = sent_pay_data.get('status')
                return bill_com_payment_id, bill_com_payment_status
        elif response and response.get('response_message') == 'Error':
            response_data = response.get('response_data',{})
            error_message = response_data.get('error_message', '')
            error_code = response_data.get('error_code', '')
            if error_code and error_code == 'BDC_1152':
                error_message = 'The process date should be in future for scheduling payment.\n Payments cannot be processed on weekends or public holidays.'
            raise UserError(_("%s") % (error_message))

    def import_bill_payments(self, bill_com_payment_import_url, filter_data):
        session_id = self.session_id
        devKey = self.devKey
        filter_data = str(filter_data)
        data = { 'sessionId': session_id,'devKey': devKey,  'data': filter_data.replace("\'",'')}
        x = requests.post(bill_com_payment_import_url, headers={"content-type":"application/x-www-form-urlencoded"}, data=data)
        response = json.loads(x.text)
        if response and response.get('response_message') == 'Success':
            response_data = response.get('response_data',{})
            return response_data
        elif response and response.get('response_message') == 'Error':
            error_message = response.get('response_data',{}).get('error_message')
            raise UserError(_("%s") % (error_message))

    def import_bills(self, bill_com_bill_import_url, filter_data):
        session_id = self.session_id
        devKey = self.devKey
        filter_data = str(filter_data)
        data = {'sessionId': session_id, 'devKey': devKey, 'data': filter_data.replace("\'", '')}
        x = requests.post(bill_com_bill_import_url,
                          headers={"content-type": "application/x-www-form-urlencoded"}, data=data)
        response = json.loads(x.text)
        if response and response.get('response_message') == 'Success':
            response_data = response.get('response_data', {})
            return response_data
        elif response and response.get('response_message') == 'Error':
            error_message = response.get('response_data', {}).get('error_message')
            raise UserError(_("%s") % (error_message))

    def cancel_bill_payments(self, bill_com_payment_cancel_url, data):
        session_id = self.session_id
        devKey = self.devKey
        data = str(data)
        data = { 'sessionId': session_id,'devKey': devKey,  'data': data.replace("\'",'')}
        x = requests.post(bill_com_payment_cancel_url, headers={"content-type":"application/x-www-form-urlencoded"}, data=data)
        response = json.loads(x.text)
        _logger.info('response %s', response)
        if response and response.get('response_message') == 'Success':
            response_data = response.get('response_data',{})
            return response_data
        elif response and response.get('response_message') == 'Error':
            error_message = response.get('response_data',{}).get('error_message')
            raise UserError(_("%s") % (error_message))

    def import_vendor_data(self, bill_com_vendor_import_url, filter_data):
        session_id = self.session_id
        devKey = self.devKey
        filter_data = str(filter_data)
        data = { 'sessionId': session_id,'devKey': devKey,  'data': filter_data.replace("\'",'')}
        x = requests.post(bill_com_vendor_import_url, headers={"content-type":"application/x-www-form-urlencoded"}, data=data)
        response = json.loads(x.text)
        if response and response.get('response_message') == 'Success':
            response_data = response.get('response_data',{})
            return response_data
        elif response and response.get('response_message') == 'Error':
            error_message = response.get('response_data',{}).get('error_message')
            raise UserError(_("%s") % (error_message))

    def import_vendor_bank_account_data(self, bill_com_vendor_bankaccount_import_url, filter_data):
        session_id = self.session_id
        devKey = self.devKey
        filter_data = str(filter_data)
        data = { 'sessionId': session_id,'devKey': devKey,  'data': filter_data.replace("\'",'')}
        x = requests.post(bill_com_vendor_bankaccount_import_url, headers={"content-type":"application/x-www-form-urlencoded"}, data=data)
        response = json.loads(x.text)
        if response and response.get('response_message') == 'Success':
            response_data = response.get('response_data',{})
            return response_data
        elif response and response.get('response_message') == 'Error':
            error_message = response.get('response_data',{}).get('error_message')
            raise UserError(_("%s") % (error_message))           

        
    def import_coa_api(self, bill_com_coa_import_url, vendor_data):
        session_id = self.session_id
        devKey = self.devKey
        vendor_data = str(vendor_data)
        data = {'sessionId': session_id,'devKey': devKey, 'data': '''%s''' %(vendor_data)}
        x = requests.post(bill_com_coa_import_url, headers={"content-type":"application/x-www-form-urlencoded"}, data=data)
        response = json.loads(x.text)
        if response and response.get('response_message') == 'Success':
            response_data = response.get('response_data',{})
            return response_data
        elif response and response.get('response_message') == 'Error':
            error_message = response.get('response_data',{}).get('error_message')
            raise UserError(_("%s") % (error_message))         