# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CrmLead(models.Model):
    _inherit = "crm.lead"

    lead_company_type = fields.Selection(
        string="Lead Company Type",
        selection=[
            ("person", "Individual"),
            ("company", "Customer Company"),
            ("owner", "Owner"),
            ("management", "Management"),
        ],
        default="company",
    )
    crm_lead_contact_ids = fields.One2many("crm.lead.contact", "crm_lead_id", string="Lead Contact")
    lead_vertical = fields.Selection(
        [
            ("res", "RES"),
            ("srl", "SRL"),
            ("local", "Local"),
            ("auto", "Auto"),
            ("agency", "Agency"),
        ],
        string="Vertical",
    )
    show_validate_btn = fields.Boolean(string="Show Validation Button", compute="_set_show_validate_btn")

    def _set_show_validate_btn(self):
        if self.crm_lead_contact_ids:
            self.show_validate_btn = True
        else:
            self.show_validate_btn = False

    def _create_partner_company_data(self, name, is_company, parent_id=False, company_type=False):
        """extract data from lead to create a partner
        :param name : name of the partner
        :param is_company : True if the partner is a company
        :param parent_id : id of the parent partner (False if no parent)
        :returns res.partner record
        """
        # email_split = tools.email_split(self.email_from)
        res = {
            "name": name,
            "user_id": self.env.context.get("default_user_id") or self.user_id.id,
            "account_user_id": self.env.context.get("default_user_id") or self.user_id.id,
            "parent_id": parent_id,
            "street": self.street,
            "street2": self.street2,
            "zip": self.zip,
            "city": self.city,
            "country_id": self.country_id.id,
            "state_id": self.state_id.id,
            "website": self.website,
            "is_company": is_company,
            "type": "contact",
            "company_type": company_type if company_type else self.lead_company_type,
            "vertical": self.lead_vertical,
        }
        return res

    def _create_partner_person_data(self, contact, parent_id=False):
        res = {
            "name": contact.name,
            "user_id": self.env.context.get("default_user_id") or self.user_id.id,
            "parent_id": parent_id,
            "phone": contact.phone,
            "email": contact.email,
            "is_company": False,
            "type": "contact",
            "company_type": "person",
        }
        return res

    def validate_lead_contacts(self):
        """
        Lead contacts need to be related to the
        new Opportunity Client Company through the res_partner_clx table
        which allows a contact to have roles at many Companies
        1. Check to see it person contact exists. Create if it does not
        2. Create the parent-child relationship in the res_partner_clx table
        """
        lead_contacts = self.crm_lead_contact_ids

        if lead_contacts:
            contact_table = self.env["res.partner"]
            # contact_company_role_table = self.env["res.partner.clx.child"]
            contact_list = []

            for contact in lead_contacts:
                search_email = contact.email
                search_name = contact.name

                if search_email:
                    results = contact_table.search(
                        ["&", ("email", "=ilike", search_email), ("company_type", "=ilike", "person")]
                    )
                    for existing in results:
                        lead = self._build_lead_contact_validation(contact, existing)
                        contact_list.append(lead)

                else:
                    results = contact_table.search(
                        ["&", ("name", "=ilike", search_name), ("company_type", "=ilike", "person")]
                    )
                    for existing in results:
                        lead = self._build_lead_contact_validation(contact, existing)
                        contact_list.append(lead)

                add_new_contact_row = self._build_lead_contact_validation(contact, False)
                contact_list.append(add_new_contact_row)

        context = dict(self._context or {})
        context["contact_list"] = contact_list
        context["search_default_lead_contact"] = 1

        res = {
            "name": "Existing Contact Warning",
            "type": "ir.actions.act_window",
            "res_model": "lead.contact.warning.wizard",
            "view_type": "form",
            "view_mode": "form",
            "search_view_id": "view_clx_lead_contact_search",
            "target": "new",
            "context": context,
        }

        return res

    def _build_lead_contact_validation(self, lead=False, existing=False):
        vals = {
            "crm_lead_contact_id": lead.id,
            "crm_lead_contact_name": lead.name,
            "existing_res_partner_id": existing.id if existing else "",
            "existing_name": existing.name if existing else "Create New " + lead.name,
            "existing_function": existing.function if existing else "",
            "existing_email": existing.email if existing else "",
            "existing_phone": existing.phone if existing else "",
            "existing_city": existing.city if existing else "",
            "existing_state": existing.state_id.code if existing else "",
        }
        return vals

    def _create_lead_partner(self):
        """Create a partner from lead data
        :returns res.partner record
        """
        Partner = self.env["res.partner"]
        # if not self.crm_lead_contact_ids:
        #     contact_name = Partner._parse_partner_name(self.email_from)[0] if self.email_from else False

        if self.partner_name:
            partner_company = Partner.create(self._create_partner_company_data(self.partner_name, True))
        elif self.partner_id:
            partner_company = self.partner_id
        else:
            partner_company = None

        # new_contact = False
        # if not existing_contact_list:
        #     new_contact = contact_table.create(self._create_partner_person_data(contact, False))
        #     contact_company_role_table.create({"parent_id": partner_company.id, "child_id": new_contact.id})
        # else:
        #     print(existing_contact_list[0].id)
        #     contact_company_role_table.create(
        #         {"parent_id": partner_company.id, "child_id": existing_contact_list[0].id}
        #     )

        if partner_company:
            return partner_company
        return Partner.create(self._create_partner_company_data(self.name, False))

    # Overriding this method so that commercial_partner_id.id (the company) is used to create the
    # lead company customer rather than default partner.id, which is the lead contact/person
    def handle_partner_assignation(self, action="create", partner_id=False):
        """Handle partner assignation during a conversion from lead to opportunity.
        if action is 'create', create new partner with contact and assign lead to new partner_id.
        otherwise assign lead to the specified partner_id

        :param list ids: leads/opportunities ids to process
        :param string action: what has to be done regarding partners (create it, assign an existing one, or nothing)
        :param int partner_id: partner to assign if any
        :return dict: dictionary organized as followed: {lead_id: partner_assigned_id}
        """
        partner_ids = {}
        for lead in self:
            if partner_id:
                lead.partner_id = partner_id
            if lead.partner_id:
                partner_ids[lead.id] = lead.partner_id.id
                continue
            if action == "create":
                partner = lead._create_lead_partner()
                partner_id = partner.commercial_partner_id.id
                partner.team_id = lead.team_id
            partner_ids[lead.id] = partner_id
        return partner_ids

    @api.onchange("name")
    def onchange_lead_name(self):
        self.partner_name = self.name
