# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2020 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import date_utils
from .connection import BillComService
import json

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.depends(
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'payment_ids', 'payment_ids.state', 'payment_ids.bill_com_payment_status')
    def _compute_amount(self):
        res = super(AccountMove, self)._compute_amount()
        payment_obj = self.env['account.payment']
        for each in self:
            if each.type == 'in_invoice':
                search_scheduled_payments = payment_obj.search([('invoice_ids', 'in',[each.id]),('bill_com_payment_status','=', 'Scheduled')])
                if search_scheduled_payments:
                    each.invoice_payment_state = 'scheduled'


    bill_com_bill_id = fields.Char('Bill.com Bill ID', copy=False)
    invoice_payment_state = fields.Selection(selection_add=[('scheduled', 'Scheduled')],
        string='Payment', store=True, readonly=True, copy=False, tracking=True,
        compute='_compute_amount')
    payment_ids = fields.Many2many('account.payment', 'account_invoice_payment_rel', 'invoice_id', 'payment_id',string="Payments", copy=False, readonly=True,
                                   help="""Technical field containing the payments for Invoices""")

    
    def check_line_description(self):
        if self._ids:
            cr = self._cr
            cr.execute("""select distinct(mv.name) from account_move_line line
            inner join account_move mv on mv.id= line.move_id
            where mv.type='in_invoice' and line.move_id in %s and line.name is null and line.exclude_from_invoice_tab=False""" ,(tuple(self.ids),))
            invoice_names = list(filter(None, map(lambda x: x[0], cr.fetchall())))
            if invoice_names:
                if len(invoice_names) == 1:
                    invoice_names = '\n'.join(invoice_names)
                    raise UserError(_("Please fill description in all invoice lines for %s.") % (invoice_names))
                else:
                    invoice_names = '\n'.join(invoice_names)    
                    raise UserError(_("Please fill description in all invoice lines for following invoices \n%s") % (invoice_names))


    def send_to_bill_com(self):
        context = self._context
        allowed_company_ids = context.get('allowed_company_ids', False)
        company_id_brw = self.env['res.company'].sudo().browse(allowed_company_ids[0])
        final_data, odoo_invoice_data = [], {}
        bill_com_config_obj = self.env['bill.com.config'].sudo().get_bill_com_config(company_id_brw.sudo().id)
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        menu = self.env.ref('account.menu_finance')
        action_id = self.env.ref('account.action_move_in_invoice_type')
        if bill_com_config_obj:
            self.check_line_description()
            for each_inv in self:
                if each_inv.type == 'in_invoice':
                    invoice_line_ids = each_inv.invoice_line_ids
                    if not invoice_line_ids:
                        raise UserError(_("You cannot send this invoice as it doesn't contains bill lines."))
                    if menu and action_id:
                        invoice_url = base_url + '/web#id=%d&action=%s&view_type=form&model=account.move&menu_id=%s' % (each_inv.id, action_id.id, menu.id)
                    else:
                        invoice_url = base_url + '/web#id=%d&view_type=form&model=account.move' % (each_inv.id)    
                    vendor_id = each_inv.partner_id
                    bill_com_vendor_id = vendor_id.bill_com_vendor_id
                    if not bill_com_vendor_id:
                        raise UserError(_("Vendor not found! If a new Vendor is created, please ensure it is pushed to Bill.com."))
                        # Following code is to create the Vendor and Vendor Bank Account Details First in the Bill.com and then generating Bill.
                        # bill_com_vendor_id = vendor_id.send_vendor_info()
                    invoice_number = each_inv.ref if each_inv.ref else each_inv.name
                    odoo_invoice_data[invoice_number] = each_inv.id
                    invoice_date = each_inv.invoice_date.strftime('%Y-%m-%d')
                    invoice_date_due = each_inv.invoice_date_due
                    if invoice_date_due:
                        invoice_date_due = invoice_date_due.strftime('%Y-%m-%d')
                    else:
                        invoice_date_due = invoice_date    
                    all_line_items = []
                    for each_line in invoice_line_ids:
                        price_subtotal = each_line.price_subtotal
                        quantity = each_line.quantity
                        name = each_line.name
                        price_unit = each_line.price_unit
                        tax_ids = each_line.tax_ids
                        price_subtotal = each_line._get_price_total_and_subtotal(price_unit=price_unit, taxes=tax_ids).get('price_total', 'price_subtotal')
                        a = {"entity": "BillLineItem","amount": price_subtotal,'description':name,"quantity": quantity, "unitPrice": price_unit}                    
                        all_line_items.append(a)
                    data = {"obj": {"entity": "Bill", "isActive" : "1", "vendorId" : bill_com_vendor_id, "invoiceNumber": invoice_number, "invoiceDate": invoice_date, "dueDate": invoice_date_due,'description': invoice_url,'poNumber': each_inv.invoice_origin or '', "billLineItems": all_line_items}}
                    final_data.append(data)
        if bill_com_config_obj and final_data:
            final_dict = {"bulk": final_data}
            final_dict = json.dumps(final_dict)
            bill_com_user_name = bill_com_config_obj.bill_com_user_name
            bill_com_password = bill_com_config_obj.bill_com_password
            bill_com_orgid = bill_com_config_obj.bill_com_orgid
            bill_com_devkey = bill_com_config_obj.bill_com_devkey
            bill_com_login_url = bill_com_config_obj.bill_com_login_url
            bill_com_bill_create_url = bill_com_config_obj.bill_com_bill_create_url
            if bill_com_bill_create_url:
                bill_com_service_obj = BillComService(bill_com_user_name, bill_com_password, bill_com_orgid, bill_com_devkey, bill_com_login_url)
                bill_com_invoice_data = bill_com_service_obj.create_update_bill_api(bill_com_bill_create_url, final_dict)
                if bill_com_invoice_data:
                    for invoice_number, bill_com_bill_id in bill_com_invoice_data.items():
                        odoo_inv_id = odoo_invoice_data.get(invoice_number)
                        self.browse(odoo_inv_id).bill_com_bill_id =  bill_com_bill_id

    def update_to_bill_com(self):
        context = self._context or {}
        if 'allowed_company_ids' in context:
            allowed_company_ids = context.get('allowed_company_ids', False)
            company_id_brw = self.env['res.company'].sudo().browse(allowed_company_ids[0])
            final_data, odoo_invoice_data = [], {}
            bill_com_config_obj = self.env['bill.com.config'].sudo().get_bill_com_config(company_id_brw.sudo().id)
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            menu = self.env.ref('account.menu_finance')
            action_id = self.env.ref('account.action_move_in_invoice_type')
            if bill_com_config_obj:
                self.check_line_description()
                for each_inv in self:
                    if each_inv.type == 'in_invoice':
                        bill_com_bill_id = each_inv.bill_com_bill_id
                        if bill_com_bill_id:
                            invoice_line_ids = each_inv.invoice_line_ids
                            if not invoice_line_ids:
                                raise UserError(_("You cannot send this invoice as it doesn't contains bill lines."))
                            if menu and action_id:
                                invoice_url = base_url + '/web#id=%d&action=%s&view_type=form&model=account.move&menu_id=%s' % (each_inv.id, action_id.id, menu.id)
                            else:
                                invoice_url = base_url + '/web#id=%d&view_type=form&model=account.move' % (each_inv.id)    
                            vendor_id = each_inv.partner_id
                            bill_com_vendor_id = vendor_id.bill_com_vendor_id
                            if not bill_com_vendor_id:
                                # Following code is to create the Vendor and Vendor Bank Account Details First in the Bill.com and then generating Bill.
                                bill_com_vendor_id = vendor_id.send_vendor_info()
                            invoice_number = each_inv.ref if each_inv.ref else each_inv.name
                            odoo_invoice_data[invoice_number] = each_inv.id
                            invoice_date = each_inv.invoice_date.strftime('%Y-%m-%d')
                            invoice_date_due = each_inv.invoice_date_due
                            if invoice_date_due:
                                invoice_date_due = invoice_date_due.strftime('%Y-%m-%d')
                            else:
                                invoice_date_due = invoice_date    
                            all_line_items = []
                            for each_line in invoice_line_ids:
                                price_subtotal = each_line.price_subtotal
                                quantity = each_line.quantity
                                name = each_line.name
                                price_unit = each_line.price_unit
                                tax_ids = each_line.tax_ids
                                price_subtotal = each_line._get_price_total_and_subtotal(price_unit=price_unit, taxes=tax_ids).get('price_total', 'price_subtotal')
                                a = {"entity": "BillLineItem","amount": price_subtotal,'description':name,"quantity": quantity, "unitPrice": price_unit}                    
                                all_line_items.append(a)
                            isActive = '2' if each_inv.state == 'draft' else '1'    
                            data = {"obj": {"entity": "Bill", "id": bill_com_bill_id, "isActive" : isActive, "vendorId" : bill_com_vendor_id, "invoiceNumber": invoice_number, "invoiceDate": invoice_date, "dueDate": invoice_date_due,'description': invoice_url,'poNumber': each_inv.invoice_origin or '', "billLineItems": all_line_items}}
                            final_data.append(data)
                if bill_com_config_obj and final_data:
                    final_dict = {"bulk": final_data}
                    final_dict = json.dumps(final_dict)
                    bill_com_user_name = bill_com_config_obj.bill_com_user_name
                    bill_com_password = bill_com_config_obj.bill_com_password
                    bill_com_orgid = bill_com_config_obj.bill_com_orgid
                    bill_com_devkey = bill_com_config_obj.bill_com_devkey
                    bill_com_login_url = bill_com_config_obj.bill_com_login_url
                    bill_com_bill_update_url = bill_com_config_obj.bill_com_bill_update_url
                    if bill_com_bill_update_url:
                        bill_com_service_obj = BillComService(bill_com_user_name, bill_com_password, bill_com_orgid, bill_com_devkey, bill_com_login_url)
                        bill_com_invoice_data = bill_com_service_obj.create_update_bill_api(bill_com_bill_update_url, final_dict)

    def button_draft(self):
        context = self._context
        res = super(AccountMove, self).button_draft()
        if 'default_type' in context:
            self.update_to_bill_com()
        return res

    def post(self):
        context = self._context
        res = super(AccountMove, self).post()
        if 'from_import_bill' not in context:
            self.update_to_bill_com()
        return res

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    
    def remove_move_reconcile(self):
        context = self._context
        if not 'from_bill_com_cancel' in context:
            for each in self:
                payment_id = each.payment_id
                if payment_id and payment_id.bill_com_payment_id:
                    raise ValidationError(_("Error! Payment has been processed via Bill.com for this Bill."))
        res = super(AccountMoveLine, self).remove_move_reconcile()
        return res