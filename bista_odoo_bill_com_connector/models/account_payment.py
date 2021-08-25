# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2020 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models, _
import time
from .connection import BillComService
import json
from datetime import timedelta, date
from odoo.exceptions import UserError, ValidationError


class account_payment(models.Model):
    _inherit = "account.payment"

    bill_com_payment_id = fields.Char('Bill.com Payment ID', copy=False)
    bill_com_payment_status = fields.Char('Bill.Com Payment Status', copy=False)
    
    @api.model
    def default_get(self, default_fields):
        rec = super(account_payment, self).default_get(default_fields)
        context = self._context or {}
        active_model = context.get('active_model', '')
        active_ids = context.get('active_ids', [])
        if active_model and active_model == 'account.move':
            selected_wrong_records = self.env[active_model].sudo().search([('id', 'in', active_ids),('bill_com_bill_id','!=', False)])
            if selected_wrong_records:
                raise ValidationError('Unauthorized Entry! Bills sent to Bill.com can only be paid in Bill.com system')
        return rec

    @api.onchange('amount', 'currency_id')    
    def _onchange_amount(self):
        res = super(account_payment, self)._onchange_amount()
        jrnl_filters = self._compute_journal_domain_and_types()
        journal_types = jrnl_filters['journal_types']
        domain_on_types = [('type', 'in', list(journal_types)), ('bill_com_journal', '=', False)]
        self.journal_id = self.env['account.journal'].search(domain_on_types, limit=1)    
        return res

    @api.onchange('journal_id')
    def _onchange_journal(self):
        selected_journal = self.journal_id
        payment_type = self.payment_type
        if selected_journal and payment_type != 'transfer':
            context = self._context or {}
            default_type = context.get('default_type', '')
            active_domain = context.get('active_domain', [])
            active_ids = context.get('active_ids', [])
            cr = self._cr
            cr.execute("select id from account_journal where bill_com_journal=True")
            bill_com_journal_ids = list(filter(None, map(lambda x: x[0], cr.fetchall())))
            bill_com_ids = self.env['account.move'].sudo().search([('id', 'in', active_ids), ('bill_com_bill_id','!=', False)])
            if bill_com_ids and (selected_journal and bill_com_journal_ids and selected_journal.id not in bill_com_journal_ids):
                raise UserError(_("To process Bill(s) that are sent to Bill.com, use Bill.com Journal."))
            elif not bill_com_ids and (selected_journal and bill_com_journal_ids and selected_journal.id in bill_com_journal_ids):
                raise UserError(_("To process Bill(s) that are not sent to Bill.com, use Bank journal other than Bill.com Journal."))
        res = super(account_payment, self)._onchange_journal()
        return res
            
    def bill_com_cancel(self):
        for each in self:
            bill_com_payment_id = each.bill_com_payment_id
            if bill_com_payment_id:
                company_id_brw = each.company_id
                bill_com_config_obj = self.env['bill.com.config'].sudo().get_bill_com_config(company_id_brw.sudo().id)
                if bill_com_config_obj:
                    bill_com_user_name = bill_com_config_obj.bill_com_user_name
                    bill_com_password = bill_com_config_obj.bill_com_password
                    bill_com_orgid = bill_com_config_obj.bill_com_orgid
                    bill_com_devkey = bill_com_config_obj.bill_com_devkey
                    bill_com_login_url = bill_com_config_obj.bill_com_login_url
                    bill_com_payment_import_url = bill_com_config_obj.bill_com_payment_import_url
                    bill_com_service_obj = BillComService(bill_com_user_name, bill_com_password, bill_com_orgid, bill_com_devkey, bill_com_login_url)
                    filter_data = { "start" : 0, "max" : 999, "filters" : [{"field":"id", "op":"=", "value": bill_com_payment_id}]}
                    filter_data = json.dumps(filter_data)
                    payment_data = bill_com_service_obj.import_bill_payments(bill_com_payment_import_url, filter_data)
                    if payment_data:
                        status = payment_data[0].get('status', '')
                        if status not in ('3', '4'):
                            raise UserError(_("You cannot cancel this payment because it is not cancelled on Bill.com"))
                        else:
                            each.with_context({'from_bill_com_cancel': True}).action_draft()
                            each.cancel()
                            each.bill_com_payment_status = 'Cancelled'

	
class payment_register(models.TransientModel):
    _inherit = 'account.payment.register'

    group_payment_invisible = fields.Boolean('Group Payment Invisible', copy=False, default=False)

    def create_payments(self):
        action_vals = super(payment_register, self).create_payments()
        if action_vals and 'domain' in action_vals:
            action_vals['domain'] = action_vals.get('domain')[:-1]    
        return action_vals


    # This function is inherited becuase wanted to raise warning for the scheduled vendor Payments.
    @api.model
    def default_get(self, fields_list):
        rec = {}
        active_ids = self._context.get('active_ids', [])
        if not active_ids:
            return rec
        account_move_obj = self.env['account.move'] 
        invoices = account_move_obj.browse(active_ids)
        payment_obj = self.env['account.payment']
        context = self._context or {}
        selected_wrong_records = account_move_obj.sudo().search([('id', 'in', active_ids),('bill_com_bill_id','!=', False)])
        if selected_wrong_records:
            raise ValidationError('Unauthorized Entry! Bills sent to Bill.com can only be paid in Bill.com system.')
        # Check all invoices are open
        if any(invoice.state != 'posted' or invoice.invoice_payment_state not in ('not_paid', 'scheduled') or not invoice.is_invoice() for invoice in invoices):
            raise UserError(_("You can only register payments for open invoices"))
        # Check all invoices are inbound or all invoices are outbound
        outbound_list = [invoice.is_outbound() for invoice in invoices]
        first_outbound = invoices[0].is_outbound()
        if any(x != first_outbound for x in outbound_list):
            raise UserError(_("You can only register at the same time for payment that are all inbound or all outbound"))
        if any(inv.company_id != invoices[0].company_id for inv in invoices):
            raise UserError(_("You can only register at the same time for payment that are all from the same company"))
        # Check the destination account is the same
        destination_account = invoices.line_ids.filtered(lambda line: line.account_internal_type in ('receivable', 'payable')).mapped('account_id')
        if len(destination_account) > 1:
            raise UserError(_('There is more than one receivable/payable account in the concerned invoices. You cannot group payments in that case.'))
        if 'invoice_ids' not in rec:
            rec['invoice_ids'] = [(6, 0, invoices.ids)]
        if 'journal_id' not in rec:
            domain_on_types = [('company_id', '=', self.env.company.id), ('type', 'in', ('bank', 'cash')), ('bill_com_journal', '=', False)]
            rec['journal_id'] = self.env['account.journal'].search(domain_on_types, limit=1).id
        if 'payment_method_id' not in rec:
            if invoices[0].is_inbound():
                domain = [('payment_type', '=', 'inbound')]
            else:
                domain = [('payment_type', '=', 'outbound')]
            rec['payment_method_id'] = self.env['account.payment.method'].search(domain, limit=1).id
        rec['payment_date'] = fields.Date.context_today(self)
        return rec

    @api.onchange('journal_id', 'invoice_ids')
    def _onchange_journal(self):
        selected_journal = self.journal_id
        if selected_journal:
            context = self._context or {}
            active_ids = context.get('active_ids', [])
            cr = self._cr
            cr.execute("select id from account_journal where bill_com_journal=True")
            bill_com_journal_ids = list(filter(None, map(lambda x: x[0], cr.fetchall())))
            bill_com_ids = self.env['account.move'].sudo().search([('id', 'in', active_ids), ('bill_com_bill_id','!=', False)])    
            if (selected_journal and bill_com_journal_ids and selected_journal.id in bill_com_journal_ids):
                if bill_com_ids and len(bill_com_ids.ids) != len(active_ids):
                    raise UserError(_("To pay via Journal - Bill.com, only unpaid bill(s) sent to Bill.com can be processed for payment"))    
                elif not bill_com_ids:
                    raise UserError(_("To process Bill(s) that are not sent to Bill.com, use Bank journal other than Bill.com Journal."))
                else:
                    self.group_payment_invisible = True                               
            elif bill_com_ids:
                raise UserError(_("To process Bill(s) that are sent to Bill.com, use Bill.com Journal."))                        
        res = super(payment_register, self)._onchange_journal()
        return res
