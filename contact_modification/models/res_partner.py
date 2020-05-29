# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64
import logging
from odoo import api, fields, models
from ast import literal_eval


class Partner(models.Model):
    _inherit = "res.partner"


    company_type = fields.Selection(string='Company Type',
        selection_add=[('company', 'Customer Company'),('owner', 'Owner'),('management', 'Management')],
        compute='_compute_company_type', inverse='_write_company_type',store=True)
    ownership_company_type_id = fields.Many2one('res.partner',string='Owner Ship Company')
    management_company_type_id = fields.Many2many('res.partner','mgmt_rel','respart_id','mgmt_id',string='Mgmt. Company')
    is_owner = fields.Boolean(string='Is a Owner', default=False,help="Check if the contact is a Owner")
    is_management = fields.Boolean(string='Is a Management', default=False,help="Check if the contact is a Management")
    secondary_user_id = fields.Many2one('res.users', string='Secondary Acct. Manager')
    national_user_id = fields.Many2one('res.users', string='National Acct. Manager')
    mangement_company_type = fields.Selection(string='Mgmt. Company Type', selection=[('greystar','Greystar'),('other','Other')])
    contact_type = fields.Selection(string='Contact type', selection=[('normal','Normal'),('proofing','Proofing Contact'),('reporting','Reporting Contact')],default='normal')
    contact_company_type_id = fields.Many2one('res.partner',string='Contact Name')
    company_type_rel = fields.Selection(related='company_type',string='Company Type',)
    childname_management = fields.Char("Management Name",compute="child_id_name_management")
    

    def child_id_name_management(self):
        for rec in self:
            if rec.management_company_type_id:
                rec.childname_management = ','.join([child.name for child in rec.management_company_type_id])
            else:
                rec.childname_management = ' '

    @api.depends('is_company','is_owner','is_management')
    def _compute_company_type(self):
        for partner in self:
            if partner.is_company and partner.is_owner == False and partner.is_management == False:
                partner.company_type = 'company'
            elif partner.is_owner and partner.is_management == False:
                partner.company_type = 'owner'
            elif partner.is_management and partner.is_owner == False:
                partner.company_type == 'management'
            else:
                partner.company_type == 'person'


    def properties_owner(self):
        self.ensure_one()
        domain = ['|',('ownership_company_type_id', '=',self.id),('ownership_company_type_id','in',self.child_ids.ids)]
        print (">>>>",self.search(domain))
        action = self.env.ref('contact_modification.action_contacts_list_owner').read()[0]
        context = literal_eval(action['context'])
        context.update(self.env.context)
        return dict(action, domain=domain, context=context)


    def properties_management(self):
        self.ensure_one()
        domain = ['|',('management_company_type_id', 'in',[self.id]),('management_company_type_id','in',self.child_ids.ids)]
        action = self.env.ref('contact_modification.action_contacts_list_managemet').read()[0]
        context = literal_eval(action['context'])
        context.update(self.env.context)
        return dict(action, domain=domain, context=context)

    def _write_company_type(self):
        for partner in self:

            if partner.company_type =='company':
                partner.is_company = True
                partner.is_management = False
                partner.is_owner = False
            if partner.company_type =='person':
                partner.is_company = False
                partner.is_management = False
                partner.is_owner = False

            if partner.company_type == 'owner':
                partner.is_owner = True
                partner.is_management = False

            if partner.company_type =='management':
                partner.is_management = True
                partner.is_owner = False


    @api.onchange('company_type')
    def onchange_company_type(self):
        if self.company_type =='company':
            self.is_company = True
            self.is_management = False
            self.is_owner = False


        if self.company_type =='person':
            self.is_company = False
            self.is_management = False
            self.is_owner = False

        if self.company_type == 'owner':
            self.is_owner = True
            self.is_management = False

        if self.company_type =='management':
            self.is_management = True
            self.is_owner = False


    