# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2020 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields, api

class BillComErrorLogs(models.Model):
    _name = 'bill.com.error.logs'
    _description = 'Bill.com Error Logs'
    _order = 'error_date desc'
    _rec_name = 'api_name'
    
    error_date = fields.Datetime('Date')
    api_name = fields.Char('API')
    error_description = fields.Text('Error Description')


    def create_error_log(self, api_name, error_description):
    	self.create({'error_date': fields.Datetime.now(), 
    				'api_name': api_name,
    				'error_description': error_description})
