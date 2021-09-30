# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from .connection import BillComService
import json

class ResPartner(models.Model):
    _inherit = 'res.partner'

    bill_com_vendor_id = fields.Char('Bill.com Vendor ID', copy=False)
    bank_ids = fields.One2many('res.partner.bank', 'partner_id', "Bank Accounts", context={'active_test': False})

    def create_write_vendor_info(self, bill_com_config_obj):
        if bill_com_config_obj:
            bill_com_user_name = bill_com_config_obj.bill_com_user_name
            if bill_com_user_name:
                bill_com_password = bill_com_config_obj.bill_com_password
                bill_com_orgid = bill_com_config_obj.bill_com_orgid
                bill_com_devkey = bill_com_config_obj.bill_com_devkey
                bill_com_login_url = bill_com_config_obj.bill_com_login_url
                bill_com_vendor_create_url = bill_com_config_obj.bill_com_vendor_create_url
                bill_com_vendor_update_url = bill_com_config_obj.bill_com_vendor_update_url
                name = self.name
                bill_com_vendor_id = self.bill_com_vendor_id
                data = {"obj": {"entity":"Vendor"}}
                if bill_com_vendor_id:
                    data["obj"].update({"id" : bill_com_vendor_id, "name" : name})
                else:    
                    data["obj"].update({"isActive" : "1", "name" : name, "payBy": "0"# By Check
                        })
                street = self.street
                data["obj"].update({"address1" : street or ''})
                street2 = self.street2
                data["obj"].update({"address2" : street2 or ''})
                city = self.city
                data["obj"].update({"addressCity" : city or ''})
                state_id = self.state_id
                if state_id:
                    data["obj"].update({"addressState" : state_id.code})
                else:
                    data["obj"].update({"addressState" : ''})
                addresszip = self.zip
                data["obj"].update({"addressZip" : addresszip or ''})
                country_id = self.country_id
                if country_id:
                    data["obj"].update({"addressCountry" : country_id.name})
                else:
                    data["obj"].update({"addressCountry" : ''})    
                email = self.email
                data["obj"].update({"email" : email or ''})
                phone = self.phone
                data["obj"].update({"phone" : phone or ''})
                data = json.dumps(data)
                bill_com_service_obj = BillComService(bill_com_user_name, bill_com_password, bill_com_orgid, bill_com_devkey, bill_com_login_url)
                if bill_com_vendor_id:
                    bill_com_vendor_id = bill_com_service_obj.create_vendor_api(bill_com_vendor_update_url, data)
                else:    
                    bill_com_vendor_id = bill_com_service_obj.create_vendor_api(bill_com_vendor_create_url, data)
                    if bill_com_vendor_id:
                        self.bill_com_vendor_id = bill_com_vendor_id
                return bill_com_vendor_id

    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        user_id_brw = self.env['res.users'].sudo().browse(self._uid)
        company_id_brw = user_id_brw.company_id
        if ('name' in vals) or ('street' in vals) or ('street2' in vals) or ('city' in vals) or ('zip' in vals) or ('state_id' in vals) or ('country_id' in vals) or ('phone' in vals) or ('email' in vals):
            bill_com_config_obj = self.env['bill.com.config'].sudo().get_bill_com_config(company_id_brw.id)
            for each in self:
                if each.supplier_rank > 0:
                    bill_com_vendor_id = each.create_write_vendor_info(bill_com_config_obj)
                    message = ("""Update on Bill.com is done by %s""" % (user_id_brw.name))
                    each.message_post(body=message)
        return res

    def send_vendor_info(self):
        company_id_brw = self.env['res.users'].sudo().browse(self._uid).company_id
        bill_com_config_obj = self.env['bill.com.config'].sudo().get_bill_com_config(company_id_brw.id)
        for each in self:
            bill_com_vendor_id = each.create_write_vendor_info(bill_com_config_obj)
            if bill_com_vendor_id:
                # search_active_bank_accounts = self.env['res.partner.bank'].search([('partner_id', '=', each.id)])
                # search_active_bank_accounts.update_on_bill_com()
                user_name = self.env['res.users'].sudo().browse(self._uid).name
                message = ("""Update on Bill.com is done by %s""" % (user_name))
                each.message_post(body=message)
                return bill_com_vendor_id