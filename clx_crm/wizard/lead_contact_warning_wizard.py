from odoo import api, fields, models


class LeadContactWarningWizard(models.TransientModel):
    _name = "lead.contact.warning.wizard"
    _description = "List of existing contacts with similar name and/or email"

    title = fields.Char()
    message = fields.Char()
    # existing_contact_ids = fields.Many2many("res.partner")
    existing_contact_ids = fields.Many2many("lead.contact.validation")

    @api.model
    def default_get(self, fields):
        res = super(LeadContactWarningWizard, self).default_get(fields)
        contact_list = self._context["contact_list"]
        # existing_contacts = self.env["res.partner"].search([("id", "in", existing_ids)])
        lead_contact_validation_ids = []

        for lead in contact_list:
            val_rec = self.env["lead.contact.validation"].create(lead)
            lead_contact_validation_ids.append(val_rec.id)

        if len(lead_contact_validation_ids) > 0:
            res.update(
                {
                    "message": "One or more contacts exists that is similar to your Lead Contact.\n\n Please select one of the following to options to proceed with the Lead to Opportunity Conversion.",
                    "existing_contact_ids": lead_contact_validation_ids,
                }
            )

        return res

    def set_validated_contacts(self):
        print("SET VALIDATED LEAD CONTACTS")
