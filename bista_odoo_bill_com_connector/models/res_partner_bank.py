# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2020 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from .connection import BillComService
import requests
import json
from odoo.exceptions import UserError, ValidationError


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'
    active = fields.Boolean('Active', default=True)
    bill_com_vendor_bank_account_id = fields.Char('Bill.Com ID', copy=False)
    bill_com_organization_bank_account_id = fields.Char('Organization Bill.Com ID', copy=False)
    _sql_constraints = [
        ('unique_number', 'unique(sanitized_acc_number, company_id)', 'Account Number must be unique'),
    ]
    supplier_rank = fields.Integer(related='partner_id.supplier_rank', copy=False, default=0)

    def valid_routing_number(self, routing_number):
        if len(routing_number) != 9:
            return 'Routing Number should be of 9 Digit.'

        if not routing_number.isnumeric():
            return 'Routing Number cannot be Alphanumeric.'

        checksum = (3 * (int(routing_number[0]) + int(routing_number[3]) + int(routing_number[6]))) + \
                   (7 * (int(routing_number[1]) + int(routing_number[4]) + int(routing_number[7]))) + \
                   (1 * (int(routing_number[2]) + int(routing_number[5]) + int(routing_number[8])))

        a = (checksum % 10) == 0
        if not a:
            return 'Invalid Routing Number.'
        

    @api.onchange('aba_routing')
    def onchange_aba_routing(self):
        aba_routing = self.aba_routing
        if aba_routing:
            value = self.valid_routing_number(aba_routing)
            if value:
                warning = {
                        'title': 'Invalid Routing Number !',
                        'message': value,
                }
                self.aba_routing = ''
                return {'warning': warning}

    def name_get(self):
        result = []
        for bank_acc in self:
            acc_number = '***'  + str(bank_acc.acc_number)[-4:]
            result.append((bank_acc.id, acc_number))
        return result
    
    def create_vendor_bank_account_info(self, bill_com_config_obj):
        if bill_com_config_obj:
            bill_com_user_name = bill_com_config_obj.bill_com_user_name
            if bill_com_user_name:
                bill_com_password = bill_com_config_obj.bill_com_password
                bill_com_orgid = bill_com_config_obj.bill_com_orgid
                bill_com_devkey = bill_com_config_obj.bill_com_devkey
                bill_com_login_url = bill_com_config_obj.bill_com_login_url
                bill_com_vendor_bank_account_create_url = bill_com_config_obj.bill_com_vendor_bank_account_create_url
                bill_com_vendor_bank_account_update_url = bill_com_config_obj.bill_com_vendor_bank_account_update_url
                bill_com_vendor_id = self.partner_id.bill_com_vendor_id
                bill_com_vendor_bank_account_id = self.bill_com_vendor_bank_account_id
                bill_com_mfa_id = bill_com_config_obj.bill_com_mfa_id
                bill_com_device_name = bill_com_config_obj.bill_com_device_name
                if bill_com_vendor_id and bill_com_mfa_id and bill_com_device_name:
                    data={"obj" : {"entity" : "VendorBankAccount", "vendorId": bill_com_vendor_id}}
                    acc_number = self.acc_number
                    if acc_number:
                        data['obj'].update({"accountNumber": acc_number})
                    aba_routing = self.aba_routing
                    if aba_routing:
                        data['obj'].update({"routingNumber": aba_routing})
                    acc_holder_name = self.acc_holder_name
                    if acc_holder_name:
                        data['obj'].update({"nameOnAcct": acc_holder_name or ''})    
                    active = self.active
                    if active:
                        data['obj'].update({"isActive": "1"})
                    bill_com_service_obj = BillComService(bill_com_user_name, bill_com_password, bill_com_orgid, bill_com_devkey, bill_com_login_url, bill_com_mfa_id, bill_com_device_name)
                    if bill_com_service_obj:
                        usersId = bill_com_service_obj.usersId
                        data['obj'].update({"usersId": str(usersId)})
                    data = json.dumps(data)
                    if bill_com_vendor_id:
                        if not bill_com_vendor_bank_account_id and active:
                            bill_com_vendor_bank_account_id = bill_com_service_obj.create_update_vendor_bank_account_api(bill_com_vendor_bank_account_create_url, data)
                            if bill_com_vendor_bank_account_id:
                                self.bill_com_vendor_bank_account_id = bill_com_vendor_bank_account_id
                            return bill_com_vendor_bank_account_id
                        elif bill_com_vendor_bank_account_id and not active:
                            data = {"id" : bill_com_vendor_bank_account_id}
                            data = json.dumps(data)
                            bill_com_service_obj = BillComService(bill_com_user_name, bill_com_password, bill_com_orgid, bill_com_devkey, bill_com_login_url, bill_com_mfa_id, bill_com_device_name)
                            bill_com_vendor_bank_account_id = bill_com_service_obj.create_update_vendor_bank_account_api(bill_com_vendor_bank_account_update_url, data)
                            self.bill_com_vendor_bank_account_id = False

    def delete_vendor_bank_account_info(self, bill_com_config_obj):
        if bill_com_config_obj:
            bill_com_user_name = bill_com_config_obj.bill_com_user_name
            if bill_com_user_name:
                bill_com_password = bill_com_config_obj.bill_com_password
                bill_com_orgid = bill_com_config_obj.bill_com_orgid
                bill_com_devkey = bill_com_config_obj.bill_com_devkey
                bill_com_login_url = bill_com_config_obj.bill_com_login_url
                bill_com_vendor_bank_account_update_url = bill_com_config_obj.bill_com_vendor_bank_account_update_url
                bill_com_vendor_bank_account_id = self.bill_com_vendor_bank_account_id
                bill_com_mfa_id = bill_com_config_obj.bill_com_mfa_id
                bill_com_device_name = bill_com_config_obj.bill_com_device_name
                if bill_com_vendor_bank_account_id and bill_com_mfa_id and bill_com_device_name:
                    data = {"id" : bill_com_vendor_bank_account_id}
                    data = json.dumps(data)
                    bill_com_service_obj = BillComService(bill_com_user_name, bill_com_password, bill_com_orgid, bill_com_devkey, bill_com_login_url, bill_com_mfa_id, bill_com_device_name)
                    bill_com_vendor_bank_account_id = bill_com_service_obj.create_update_vendor_bank_account_api(bill_com_vendor_bank_account_update_url, data)
                    self.bill_com_vendor_bank_account_id = False

    def update_on_bill_com(self):
        res_user_obj = self.env['res.users']
        for each in self:
            partner_id = each.partner_id
            if partner_id.bill_com_vendor_id:
                company_id_brw = self.env['res.users'].sudo().browse(self._uid).company_id
                bill_com_config_obj = self.env['bill.com.config'].sudo().get_bill_com_config(company_id_brw.id)
                each.create_vendor_bank_account_info(bill_com_config_obj)
                user_name = res_user_obj.sudo().browse(self._uid).name
                message = ("""Update of Bank Account(%s) on Bill.com is done by %s""" % (each.id, user_name))
                partner_id.message_post(body=message)
            else:
                partner_id.send_vendor_info()    

    def read(self, fields=None, load='_classic_read'):
        result = super(ResPartnerBank, self).read(fields, load=load)
        for record in result:
            if record.get('acc_number'):
                record['acc_number'] = '***'  + str(record['acc_number'])[-4:]
        return result

    @api.model
    def default_get(self, fields):
        res = super(ResPartnerBank, self).default_get(fields)
        context = self._context
        if 'acc_holder_name' in context:
            acc_holder_name = context.get('acc_holder_name')
            res['acc_holder_name'] = acc_holder_name
        return res

    # @api.model    
    # def create(self, vals):
    #     context = self._context
    #     res = super(ResPartnerBank, self).create(vals)
    #     if 'default_partner_id' not in context:
    #         company_id_brw = self.env['res.users'].sudo().browse(self._uid).company_id
    #         if isinstance(vals, list):
    #             vals = vals[0]
    #         if 'active' in vals:
    #             bill_com_config_obj = self.env['bill.com.config'].sudo().get_bill_com_config(company_id_brw.id)
    #             if vals.get('active'):
    #                 for each in res:
    #                     each.create_vendor_bank_account_info(bill_com_config_obj)
    #     return res

    # def write(self, vals):
    #     res = super(ResPartnerBank, self).write(vals)
    #     context = self._context
    #     if 'default_partner_id' not in context:
    #         company_id_brw = self.env['res.users'].sudo().browse(self._uid).company_id
    #         if 'active' in vals:
    #             bill_com_config_obj = self.env['bill.com.config'].sudo().get_bill_com_config(company_id_brw.id)
    #             if not vals.get('active'):
    #                 for each in self:
    #                     bill_com_vendor_id = each.delete_vendor_bank_account_info(bill_com_config_obj)
    #             else:
    #                 for each in self:
    #                     bill_com_vendor_id = each.create_vendor_bank_account_info(bill_com_config_obj)
    #     return res

    def unlink(self):
        for each_rec in self:
            bill_com_vendor_bank_account_id = each_rec.bill_com_vendor_bank_account_id
            if bill_com_vendor_bank_account_id:
                raise ValidationError(_('You cannot Delete record as it is updated on the Bill.com. Instead of Deleting it, you can make it as "InActive".'))
        return super(ResPartnerBank, self).unlink()    
        
    @api.constrains('active')
    def _check_boolean(self):
    	for each in self:
            if each.active:
    	        existing_active_rec = self.env['res.partner.bank'].search([('id', '!=', each.id), ('partner_id', '=', self.partner_id.id), ('partner_id.supplier_rank', '>', 0), ('active', '=', True)], limit=1)
    	        if existing_active_rec:
    	            raise ValidationError(_("Active account already exists. Please make it inactive and then process further."))
