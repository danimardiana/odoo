# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from ast import literal_eval

from odoo import api, fields, models


class ContactType(models.Model):
    _name = "contact.type"

    name = fields.Char('Name')
    nik = fields.Char('Nik')


class Partner(models.Model):
    _inherit = "res.partner"

    def _dafault_parent(self):
        return [(6, 0, self.parent_id.ids)]

    company_type = fields.Selection(
        string='Company Type',
        selection_add=[
            ('company', 'Customer Company'),
            ('owner', 'Owner'),
            ('management', 'Management'),
            ('vendor', 'Vendor')
        ],
        compute='_compute_company_type',
        inverse='_write_company_type', store=True)
    ownership_company_type_id = fields.Many2one(
        'res.partner', string='Owner Ship Company')
    management_company_type_id = fields.Many2one(
        'res.partner', string='Mgmt. Company')
    is_owner = fields.Boolean(
        string='Is a Owner', default=False,
        help="Check if the contact is a Owner")
    is_management = fields.Boolean(
        string='Is a Management', default=False,
        help="Check if the contact is a Management")
    is_vendor = fields.Boolean(
        string='Is a Vendore', default=False,
        help="Check if the contact is a Vendor")
    account_user_id = fields.Many2one('res.partner',
                                      string='Account Manager')
    secondary_user_id = fields.Many2one('res.partner',
                                        string='Secondary Acct. Manager')
    national_user_id = fields.Many2one('res.partner',
                                       string='National Acct. Manager')
    mangement_company_type = fields.Selection(
        string='Mgmt. Company Type',
        selection=[
            ('greystar', 'Greystar'),
            ('other', 'Other')
        ])
    contact_type_ids = fields.Many2many(
        'contact.type', 'contact_type_rel',
        'con_id', 'type_id', string="Contact Type")
    contact_company_type_id = fields.Many2one('res.partner',
                                              string='Contact Name')
    company_type_rel = fields.Selection(related='company_type',
                                        string='Company Type', )
    contact_display_kanban = fields.Char("Contact Display Name")
    contact_child_ids = fields.One2many(
        'res.partner.clx.child', 'parent_id',
        string="Other Contacts")
    vertical = fields.Char(string="Vertical")
    branding_name = fields.Char(string="Branding Name")
    timezone_char = fields.Char(string="Timezone2")
    yardi_code = fields.Char(string="Yardi Code")

    @api.onchange('contact_company_type_id')
    def onchange_contact_company_type_id(self):
        if self.contact_company_type_id:
            self.street = self.contact_company_type_id.street or ''
            self.street2 = self.contact_company_type_id.street2 or ''
            self.state_id = self.contact_company_type_id.state_id.id or False
            self.zip = self.contact_company_type_id.zip or ''
            self.city = self.contact_company_type_id.city or ''
            self.country_id = self.contact_company_type_id.country_id.id or False
            self.email = self.contact_company_type_id.email or ''
            self.phone = self.contact_company_type_id.phone or False
            self.mobile = self.contact_company_type_id.mobile or False
            self.name = self.contact_company_type_id.display_name

    @api.onchange('contact_type_ids')
    def onchange_contact_display_name(self):
        for rec in self:
            if rec.contact_type_ids:
                rec.contact_display_kanban = ' ,'.join([
                    contact.nik for contact in rec.contact_type_ids
                ])
            else:
                rec.contact_display_kanban = ''

    @api.depends('is_company', 'is_owner', 'is_management')
    def _compute_company_type(self):
        for partner in self:
            if partner.is_company and not partner.is_owner and \
                    not partner.is_management and not partner.is_vendor:
                partner.company_type = 'company'
            elif partner.is_owner and not partner.is_management and \
                    not partner.is_vendor:
                partner.company_type = 'owner'
            elif partner.is_management and not partner.is_owner and \
                    not partner.is_vendor:
                partner.company_type = 'management'
            elif partner.is_vendor and not partner.is_owner and \
                    not partner.is_management:
                partner.company_type = 'vendor'
            else:
                partner.company_type = 'person'

    def properties_owner(self):
        self.ensure_one()
        domain = [
            '|', ('ownership_company_type_id', '=', self.id),
            ('ownership_company_type_id', 'in', self.child_ids.ids)
        ]
        action = self.env.ref(
            'contact_modification.action_contacts_list_owner'
        ).read()[0]
        context = literal_eval(action['context'])
        context.update(self.env.context)
        return dict(action, domain=domain, context=context)

    def properties_management(self):
        self.ensure_one()
        domain = [
            '|', ('management_company_type_id', 'in', [self.id]),
            ('management_company_type_id', 'in', self.child_ids.ids)
        ]
        action = self.env.ref(
            'contact_modification.action_contacts_list_managemet'
        ).read()[0]
        context = literal_eval(action['context'])
        context.update(self.env.context)
        return dict(action, domain=domain, context=context)

    def _write_company_type(self):
        for partner in self:
            if partner.company_type == 'company':
                partner.is_company = True
                partner.is_management = False
                partner.is_owner = False

            if partner.company_type == 'person':
                partner.is_company = False
                partner.is_management = False
                partner.is_owner = False

            if partner.company_type == 'vendor':
                partner.is_owner = False
                partner.is_management = False
                partner.is_vendor = True

            if partner.company_type == 'owner':
                partner.is_owner = True
                partner.is_management = False
                partner.is_vendor = False

            if partner.company_type == 'management':
                partner.is_management = True
                partner.is_owner = False
                partner.is_vendor = False

    @api.onchange('company_type')
    def onchange_company_type(self):
        if self.company_type == 'company':
            self.is_company = True
            self.is_management = False
            self.is_owner = False
            self.is_vendor = False

        if self.company_type == 'person':
            self.is_company = False
            self.is_management = False
            self.is_owner = False
            self.is_vendor = False

        if self.company_type == 'owner':
            self.is_owner = True
            self.is_management = False
            self.is_vendor = False
            # self.is_company = True

        if self.company_type == 'vendor':
            self.is_owner = False
            self.is_management = False
            self.is_vendor = True
            self.supplier_rank = 1

        if self.company_type == 'management':
            self.is_management = True
            self.is_owner = False
            self.is_vendor = False
            # self.is_company = True
