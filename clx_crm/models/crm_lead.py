# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


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
    lead_contact_count = fields.Char(string="Contacts", compute="_count_contacts", store=False)

    def _set_show_validate_btn(self):
        show_validation_button = False

        if self.crm_lead_contact_ids:
            for contact in self.crm_lead_contact_ids:
                if not contact.validated:
                    show_validation_button = True

        self.show_validate_btn = show_validation_button

    def _count_contacts(self):
        for rec in self:
            if rec.crm_lead_contact_ids.ids:
                rec.lead_contact_count = str(len(rec.crm_lead_contact_ids.ids))
            else:
                rec.lead_contact_count = str(0)

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
            "function": contact.function,
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
        lead_contact_validation_ids = []

        if lead_contacts:
            contact_table = self.env["res.partner"]
            contact_list = []

            """
            Validate Contacts listed in the Lead Form by checking the database to see if:
                1) Do any existing contacts have the same email address. We should not
                create new contacts with the same email address.
                2) Do any existing contact have the same name
            Matches will be presented to the user where they make a choice to link to 
            an existing contact or create a new contact.
            """
            for contact in lead_contacts:
                if not contact.name:
                    raise ValidationError(_("Contact name missing! Please provide a name for the lead contact."))

                if not contact.validated:
                    search_email = contact.email
                    search_name = contact.name + "%"
                    results = {}

                    if search_email:
                        results = contact_table.search(
                            ["&", ("email", "ilike", search_email), ("company_type", "=", "person")]
                        )
                        if not results:
                            contact.update({"existing_contact_id": 0, "validated": True})

                        for existing in results:
                            lead = self._build_lead_contact_validation(contact, existing)
                            contact_list.append(lead)
                    else:
                        results = contact_table.search(
                            ["&", ("name", "ilike", search_name), ("company_type", "=", "person")]
                        )
                        if not results:
                            contact.update({"existing_contact_id": 0, "validated": True})

                        for existing in results:
                            lead = self._build_lead_contact_validation(contact, existing)
                            contact_list.append(lead)

                    if not search_email and results:
                        add_new_contact_row = self._build_lead_contact_validation(contact, False)
                        contact_list.append(add_new_contact_row)
                    # elif not contact_list:

            for lead in contact_list:
                val_rec = self.env["lead.contact.validation"].create(lead)
                lead_contact_validation_ids.append(val_rec.id)

        existing_contact_view_id = self.env.ref("clx_crm.view_clx_existing_contact").id
        context = dict(self._context or {})
        context["group_by"] = "crm_lead_contact_name"

        if lead_contact_validation_ids:
            return {
                "type": "ir.actions.act_window",
                "name": "Existing Contact Warning",
                "res_model": "lead.contact.validation",
                "context": context,
                "views": [(existing_contact_view_id, "tree")],
                "domain": [("id", "in", lead_contact_validation_ids)],
                "target": "new",
            }

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
        partner_table = self.env["res.partner"]
        contact_role_relationship_table = self.env["res.partner.clx.child"]

        if self.partner_name:
            partner_company = partner_table.create(self._create_partner_company_data(self.partner_name, True))
        elif self.partner_id:
            partner_company = self.partner_id
        else:
            partner_company = None

        for lead_contact in self.crm_lead_contact_ids:

            # Create role relationship with existing contact
            if lead_contact.existing_contact_id > 0:
                new_contact_role_relationship = contact_role_relationship_table.create(
                    {"parent_id": partner_company.id, "child_id": lead_contact.existing_contact_id}
                )
                if lead_contact.role:
                    new_contact_role_relationship.update({"contact_type_ids": [lead_contact.role]})

            # Create a new contact with role relationship
            else:
                new_contact = partner_table.create(self._create_partner_person_data(lead_contact, False))
                new_contact_role_relationship = contact_role_relationship_table.create(
                    {"parent_id": partner_company.id, "child_id": new_contact.id}
                )
                if lead_contact.role:
                    new_contact_role_relationship.update({"contact_type_ids": [lead_contact.role]})

        if partner_company:
            return partner_company
        return partner_table.create(self._create_partner_company_data(self.name, False))

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
