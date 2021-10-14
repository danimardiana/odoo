# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from ast import literal_eval
from lxml import etree
from odoo import api, fields, models


class ContactType(models.Model):
    _name = "contact.type"
    _description = "Contact Type"

    name = fields.Char("Name")
    nik = fields.Char("Nik")


class Partner(models.Model):
    _inherit = "res.partner"

    @api.model
    def default_get(self, fields):
        result = super(Partner, self).default_get(fields)
        country_id = self.env["res.country"].search([("code", "=", "US")])
        if country_id:
            result.update({"country_id": country_id.id})
        return result

    def _dafault_parent(self):
        return [(6, 0, self.parent_id.ids)]

    def _compute_task_count(self):
        fetch_data = self.env["project.task"].read_group(
            [("partner_id", "in", self.ids), ("parent_id", "=", False)], ["partner_id"], ["partner_id"]
        )
        result = dict((data["partner_id"][0], data["partner_id_count"]) for data in fetch_data)
        for partner in self:
            partner.task_count = result.get(partner.id, 0) + sum(c.task_count for c in partner.child_ids)

    company_type = fields.Selection(
        string="Company Type",
        store=True,
        compute="_compute_company_type",
        selection_add=[
            ("company", "Customer Company"),
            ("owner", "Owner"),
            ("management", "Management"),
            ("vendor", "Vendor"),
        ],
        inverse="_write_company_type",
    )
    ownership_company_type_id = fields.Many2one("res.partner", string="Owner Ship Company")
    management_company_type_id = fields.Many2one("res.partner", string="Mgmt. Company")
    is_owner = fields.Boolean(string="Is a Owner", default=False, help="Check if the contact is a Owner")
    is_management = fields.Boolean(string="Is a Management", default=False, help="Check if the contact is a Management")
    is_vendor = fields.Boolean(string="Is a Vendore", default=False, help="Check if the contact is a Vendor")
    is_greystar_company = fields.Boolean(string="Is a Greystar company", default=False)
    account_user_id = fields.Many2one("res.users", string="Account Manager")
    secondary_user_id = fields.Many2one("res.users", string="Secondary Acct. Manager")
    national_user_id = fields.Many2one("res.users", string="National Acct. Manager")
    national_mgr_hidden = fields.Boolean(
        string="National Manager Hidden",
        compute="_compute_national_mgr_hidden",
        help="Used to toggle the national managed field show/hide",
    )
    mangement_company_type = fields.Selection(
        string="Mgmt. Company Type", selection=[("greystar", "Greystar"), ("other", "Other")]
    )
    contact_type_ids = fields.Many2many("contact.type", "contact_type_rel", "con_id", "type_id", string="Contact Role")
    contact_company_type_id = fields.Many2one("res.partner", string="Contact Name")
    company_type_rel = fields.Selection(
        related="company_type",
        string="Company Type",
    )
    contact_display_kanban = fields.Char("Contact Display Name")
    contact_child_ids = fields.One2many("res.partner.clx.child", "parent_id", string="Other Contacts")
    vertical = fields.Selection(
        [("res", "RES"), ("srl", "SRL"), ("local", "Local"), ("auto", "Auto"), ("agency", "Agency")], string="Vertical"
    )

    branding_name = fields.Char(string="Branding Name")
    timezone_char = fields.Selection(
        [
            ("atlantic", "Atlantic"),
            ("central", "Central"),
            ("cst", "CST"),
            ("eastern", "Eastern"),
            ("est", "EST"),
            ("hawaii", "Hawaii"),
            ("mountain", "Mountain"),
            ("pacific", "Pacific"),
            ("pst", "PST"),
        ],
        string="Timezone2",
    )
    yardi_code = fields.Char(string="Yardi Code")
    fb_account = fields.Char(string="Facebook Account")
    google_ads_account = fields.Char(string="Google ADS Account")
    master_id = fields.Char(string="Master ID")
    ads_link_ids = fields.One2many("ads.link", "partner_id", string="Ads Link")
    cs_notes = fields.Text(string="CS Notes")
    ops_notes = fields.Text(string="Ops Notes")
    cat_notes = fields.Text(string="Cat Notes")
    accounting_notes = fields.Text(string="Accounting Notes")
    merchant_number = fields.Char(string="Ops Merchant Number")
    tap_clicks_username = fields.Char(string="TapClicks Username")
    tap_clicks_password = fields.Char(string="TapClicks Password")
    call_rail_destination_number = fields.Char(string="Extra Info")
    client_provided_tracking_email = fields.Char(string="Client-Provided Tracking Email")
    client_provided_utm_tracking_urls = fields.Char(string="Client-Provided UTM Tracking URLs")
    art_assets = fields.Char(string="Art Assets")
    google_analytics_cl_account_location = fields.Selection(
        [
            ("greystaranalytics@conversionlogix.com", "greystaranalytics@conversionlogix.com"),
            ("Ave5analytics@clxmedia.com", "Ave5analytics@clxmedia.com"),
            ("RESdata@conversionlogix.com", "RESdata@conversionlogix.com"),
            ("SRLdata@conversionlogix.com", "SRLdata@conversionlogix.com"),
            ("Localdata@conversionlogix.com", "Localdata@conversionlogix.com"),
            ("Autodata@conversionlogix.com", "Autodata@conversionlogix.com"),
            ("RESanalytics@clxmedia.com", "RESanalytics@clxmedia.com"),
            ("Resanalytics2@clxmedia.com", "Resanalytics2@clxmedia.com"),
            ("Resanalytics3@clxmedia.com", "Resanalytics3@clxmedia.com"),
            ("reporting@conversionlogix.com", "reporting@conversionlogix.com"),
            ("reporting1@conversionlogix.com", "reporting1@conversionlogix.com"),
            ("reporting2@conversionlogix.com", "reporting2@conversionlogix.com"),
            ("cd1@adsupnow.com", "cd1@adsupnow.com"),
            ("cd2@adsupnow.com", "cd2@adsupnow.com"),
            ("cd3@adsupnow.com", "cd3@adsupnow.com"),
            ("cd4@adsupnow.com", "cd4@adsupnow.com"),
            ("cd5@adsupnow.com", "cd5@adsupnow.com"),
            ("Missing: pursue", "Missing: pursue"),
            ("Missing: abandoned", "Missing: abandoned"),
        ],
        string="Google Analytics CL Account Location",
    )
    dni = fields.Text(string="DNI")
    submitted_platform_id = fields.Many2one("submitted.platform", string="Submittal Platform")
    invoice_template_line1 = fields.Char(string="Line1")
    invoice_template_line2 = fields.Char(string="Line2")

    # discounts block
    is_flat_discount = fields.Boolean(string="Is Flat Discount")
    clx_category_id = fields.Many2one("product.category", string="Category for Flat Discount")
    flat_discount = fields.Float(string="Flat Discount")
    is_percent_discount = fields.Boolean(string="Is Percent Discount")
    flat_discount_product = fields.Many2one(
        "product.product", string="Product for Flat Discount", help="Product the Flat Discount will be assigned to"
    )
    percent_discount = fields.Float(string="Percent Discount")
    percent_discount_category_id = fields.Many2one("product.category", string="Category for Percent Discount")
    percent_discount_product = fields.Many2one(
        "product.product",
        string="Product for Percent Discount",
        help="Product the Percent Discount will be assigned to",
    )
    discount_on_order_line = fields.Float(string="Discount on Sale Order Line (%)")
    discount_product = fields.Many2one(
        "product.product", string="Product for Flat Discount", help="Product the Main Discont will be assigned to"
    )

    client_services_team = fields.Selection(
        [("emerging_accounts", "Emerging Accounts"), ("national_accounts", "National Accounts")],
        default="emerging_accounts",
        string="Client Services Team",
    )
    implementation_specialist_id = fields.Many2one("res.users", string="Implementation Specialist - Customer Success")
    legal_name = fields.Char(string="Legal Name")
    lead_management_system = fields.Many2one("lead.management.system", string="Lead Management System")
    company_type_hidden = fields.Boolean(string="Is radio button hidden", compute="_compute_company_type_hidden")

    def open_submitted_req_form(self):
        request_forms = self.env["request.form"].search([("partner_id", "=", self.id), ("state", "=", "submitted")])
        if request_forms:
            action = self.env.ref("clx_task_management.action_request_form_submitted").read()[0]
            action["context"] = {"create": False}
            if len(request_forms) > 1:
                action["domain"] = [("id", "in", request_forms.ids)]
            elif len(request_forms) == 1:
                form_view = [(self.env.ref("clx_task_management.request_form_form_view").id, "form")]
                if "views" in action:
                    action["views"] = form_view + [(state, view) for state, view in action["views"] if view != "form"]
                else:
                    action["views"] = form_view
                action["res_id"] = request_forms.ids[0]
            else:
                action = {"type": "ir.actions.act_window_close"}
            return action

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if "custom_filter_groupby" in self._context and "parent_id" in groupby:
            domain = [("company_type", "=", "person")]
        return super(Partner, self).read_group(
            domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy
        )

    @api.model
    def create(self, vals):
        res = super(Partner, self).create(vals)

        """
        COMPANY CONTACT CREATED-CLXDB SYNC
        Only create non-system-users (no employees) contact in CLXDB
        """
        if res.company_type in {"management", "company", "person", "owner"}:
            # If the account mgr field is set, get the account mgr contact's email
            if res.account_user_id.id:
                acc_partner_id = self.env["res.users"].search([("id", "=", vals.get("account_user_id", False))])
                vals["acc_mgr_email"] = acc_partner_id.partner_id.email

            vals["contact"] = res
            CLXDB = self.env["clx.mysql"]
            CLXDB.create_contact(vals)

        return res

    def write(self, vals):
        res = super(Partner, self).write(vals)

        # if entity name changes, update opp form
        # so name in nav breadcrumb matches
        if vals.get("name", False):
            opp_lead_forms = self.env["crm.lead"].search([("partner_id", "=", self.id)])
            for opp in opp_lead_forms:
                opp.update({"name": vals.get("name", False)})

        """
        If the national account manager is changed at the manamement company
        level, then update the national manager on all it's childeren. Greystar
        is currently a special use case because it have a master management company
        """
        if vals.get("national_user_id", False):
            new_national_mgr = vals["national_user_id"]
            subsidiary_companies = {}

            if self.company_type == "management" and self.mangement_company_type != "greystar":
                subsidiary_companies = self.env["res.partner"].search([("management_company_type_id", "=", self.id)])

            elif self.id == 29824:  # Master Greystar Entity
                greystar_regional_mgmt_companies = self.env["res.partner"].search(
                    [("mangement_company_type", "=", "greystar")]
                )
                subsidiary_companies = self.env["res.partner"].search(
                    [("management_company_type_id", "in", greystar_regional_mgmt_companies.ids)]
                )

            for company in subsidiary_companies:
                company.write({"national_user_id": new_national_mgr})
        """
        ODOO ACCOUNT MGR EMAIL UPDATED-CLXDB SYNC
        if an account manager's email changes, sync the new 
        email to the company contacts in CLXDB
        """
        if self.user_ids.id and vals.get("email", False):
            cr = self._cr
            # check to see if user is an account manager for any companies
            query = """SELECT id 
                       FROM res_partner 
                       WHERE account_user_id ='%s';""" % (
                self.user_ids.id,
            )
            cr.execute(query)
            company_ids = list(filter(None, map(lambda x: x, cr.fetchall())))
            company_list = self.env["res.partner"].search([("id", "in", company_ids)])

            for company in company_list:
                vals["contact"] = company
                vals["acc_mgr_email"] = vals["email"]
                CLXDB = self.env["clx.mysql"]
                CLXDB.update_contact(vals)

        """
        COMPANY CONTACT UPDATED-CLXDB SYNC
        Only send updates to CLXDB for non-system-user contacts (no employees)
        """
        if not self.user_ids.id:
            contact_fields = {
                "name",
                "company_type",
                "parent_id",
                "street",
                "city",
                "vertical",
                "yardi_code",
                "website",
                "account_user_id",
            }

            for key in vals:
                if key == "account_user_id":
                    acc_partner_id = self.env["res.users"].search([("id", "=", vals.get("account_user_id", False))])
                    vals["acc_mgr_email"] = acc_partner_id.partner_id.email

                if key in contact_fields:
                    vals["contact"] = self

                    CLXDB = self.env["clx.mysql"]
                    CLXDB.update_contact(vals)
                    break

        return res

    @api.onchange("ownership_company_type_id")
    def onchange_ownership_company_type_id(self):
        if (self.ownership_company_type_id) and ("Greystar" in self.ownership_company_type_id.name):
            self.is_greystar_company = True
        else:
            self.is_greystar_company = False

    @api.onchange("contact_company_type_id")
    def onchange_contact_company_type(self):
        if self.contact_company_type_id:
            self.street = self.contact_company_type_id.street or ""
            self.street2 = self.contact_company_type_id.street2 or ""
            self.state_id = self.contact_company_type_id.state_id.id or False
            self.zip = self.contact_company_type_id.zip or ""
            self.city = self.contact_company_type_id.city or ""
            self.country_id = self.contact_company_type_id.country_id.id or False
            self.email = self.contact_company_type_id.email or ""
            self.phone = self.contact_company_type_id.phone or False
            self.mobile = self.contact_company_type_id.mobile or False
            self.name = self.contact_company_type_id.display_name

    @api.onchange("management_company_type_id")
    def onchange_management_company_type_id(self):
        if self.management_company_type_id and self.management_company_type_id.property_product_pricelist:
            self.property_product_pricelist = self.management_company_type_id.property_product_pricelist.id

        if self.company_type == "company" and self.management_company_type_id:
            mgmt_company = self.env["res.partner"].search([("id", "=", self.management_company_type_id.id)])

            if mgmt_company.national_user_id and mgmt_company.mangement_company_type != "greystar":
                self.national_user_id = mgmt_company.national_user_id
            elif mgmt_company.mangement_company_type == "greystar":
                greystar_master_mgmt_company = self.env["res.partner"].search([("id", "=", 29824)])

                if greystar_master_mgmt_company.national_user_id:
                    self.national_user_id = greystar_master_mgmt_company.national_user_id

    @api.onchange("contact_type_ids")
    def onchange_contact_display_name(self):
        for rec in self:
            if rec.contact_type_ids:
                rec.contact_display_kanban = " ,".join([contact.nik for contact in rec.contact_type_ids])
            else:
                rec.contact_display_kanban = ""

    # Override the inherited method
    # On new contact creationg do not set company_type
    # by default. User is required to make the selection
    @api.depends("is_company", "is_owner", "is_management")
    def _compute_company_type(self):
        for partner in self:
            if partner.is_company and not partner.is_owner and not partner.is_management:
                partner.company_type = "company"
            elif partner.is_owner and not partner.is_management:
                partner.company_type = "owner"
            elif partner.is_management and not partner.is_owner:
                partner.company_type = "management"

    def _compute_national_mgr_hidden(self):
        if (
            self.company_type == "company"
            or (self.company_type == "management" and self.mangement_company_type != "greystar")
            or self.id == 29824  # Master Greystar Entity
        ):
            self.national_mgr_hidden = False
        else:
            self.national_mgr_hidden = True

    def _compute_company_type_hidden(self):
        if (
            self.company_type == "person"
            or self.company_type == "company"
            or self.company_type == "management"
            or self.company_type == "owner"
        ):
            self.company_type_hidden = True
        else:
            self.company_type_hidden = False

    def properties_owner(self):
        self.ensure_one()
        domain = [
            "|",
            ("ownership_company_type_id", "=", self.id),
            ("ownership_company_type_id", "in", self.child_ids.ids),
        ]
        action = self.env.ref("contact_modification.action_contacts_list_owner").read()[0]
        context = literal_eval(action["context"])
        context.update(self.env.context)
        return dict(action, domain=domain, context=context)

    def properties_management(self):
        self.ensure_one()
        domain = [
            "|",
            ("management_company_type_id", "in", [self.id]),
            ("management_company_type_id", "in", self.child_ids.ids),
        ]
        action = self.env.ref("contact_modification.action_contacts_list_managemet").read()[0]
        context = literal_eval(action["context"])
        context.update(self.env.context)
        return dict(action, domain=domain, context=context)

    def assignation_management(self):
        self.ensure_one()
        clx_child_ids = self.env["res.partner.clx.child"].search([("child_id", "=", self.id)])
        domain = [("id", "in", clx_child_ids.ids)]
        action = self.env.ref("contact_modification.action_partner_assignation_contacts").read()[0]
        context = literal_eval(action["context"])
        context.update(self.env.context)
        return dict(action, domain=domain, context=context)

    def _write_company_type(self):
        for partner in self:
            partner.set_contact_type_flag()

    @api.onchange("company_type")
    def onchange_company_type(self):
        self.set_contact_type_flag()

    def set_contact_type_flag(self):
        """
        To check current contact type
        to display parent for contact at form and in relation.
        :return: None
        """
        cmp_type = self.company_type
        self.is_company = True if cmp_type == "company" else False
        self.is_vendor = True if cmp_type == "vendor" else False
        self.is_owner = True if cmp_type == "owner" else False
        self.is_management = True if cmp_type == "management" else False
