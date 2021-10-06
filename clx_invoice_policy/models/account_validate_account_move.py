from odoo import models, api, _
from odoo.exceptions import UserError


class ValidateAccountMove(models.TransientModel):
    _name = "validate.account.move"

    def validate_move(self):
        try:
            super(ValidateAccountMove, self).validate_move()
        except Exception as e:
            if self._context.get('active_model') == 'account.move':
                domain = [('id', 'in', self._context.get('active_ids', [])), ('state', 'in', ('draft','approved_draft'))]
            elif self._context.get('active_model') == 'account.journal':
                domain = [('journal_id', '=', self._context.get('active_id')), ('state', '=', 'draft')]
            else:
                raise UserError(_("Missing 'active_model' in context."))

            moves = self.env['account.move'].search(domain).filtered('line_ids')
            if not moves:
                raise UserError(_('There are no journal items in the draft or Aprroved Draft state to post.'))
            moves.post()
            return {'type': 'ir.actions.act_window_close'}