from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class BulkSendBillCom(models.TransientModel):
    """
    This wizard is used send the Invoices to the Bill.com in Bulk.
    """
    _name = 'bulk.send.bill.com'
    _description = 'Bulk Send to Bill.com'

    @api.model
    def fields_view_get(self,view_id=None, view_type=False, toolbar=False, submenu=False):
        res = super(BulkSendBillCom, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        context = self._context
        active_ids = context.get('active_ids')
        active_model = context.get('active_model')
        if active_ids and active_model == 'account.move':
            selected_wrong_records = self.env[active_model].sudo().search([('id', 'in', active_ids),'|', '|','|',('type', '!=', 'in_invoice'),('state','!=', 'posted'), ('bill_com_bill_id','!=', False), ('invoice_payment_state', '!=', 'not_paid')])
            if selected_wrong_records:
                raise ValidationError('Please select only Posted, Not Paid and not sent to Bill.com Vendor invoices.')
            non_bill_com_vendor_ids = self.env[active_model].sudo().search([('id', 'in', active_ids), ('partner_id.bill_com_vendor_id','=', False)])
            if non_bill_com_vendor_ids:
                raise ValidationError('Vendor not found! If a new Vendor is created, please ensure it is pushed to Bill.com.')
        return res

    def bulk_send_bill_com_btn(self):
        context = self._context
        active_ids = context.get('active_ids')
        invoice_brw = self.env['account.move'].sudo().browse(active_ids)
        invoice_brw.check_line_description()
        invoice_brw.send_to_bill_com()