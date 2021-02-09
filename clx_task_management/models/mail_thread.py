from odoo import models


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _notify_by_email_add_values(self, base_mail_values):
        res = super(MailThread, self)._notify_by_email_add_values(base_mail_values)
        if self._table == 'project_task' and self._module == 'clx_task_management':
            subject = self.partner_id.name + " : " + self.name
            res.update({'subject': subject})
        return res
