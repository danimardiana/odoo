# -*- coding: utf-8 -*-
# CLX
from odoo import fields, models, api


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    #overwrite the followers getting function to not send to followers
    def _notify_compute_recipients(self, message, msg_vals):

        return {
            'partners': [],
            'channels': [],
        }

        """ Compute recipients to notify based on subtype and followers. This
        method returns data structured as expected for ``_notify_recipients``. """
        msg_sudo = message.sudo()
        # get values from msg_vals or from message if msg_vals doen't exists
        pids = msg_vals.get(
            'partner_ids', []) if msg_vals else msg_sudo.partner_ids.ids
        cids = msg_vals.get(
            'channel_ids', []) if msg_vals else msg_sudo.channel_ids.ids
        message_type = msg_vals.get(
            'message_type') if msg_vals else msg_sudo.message_type
        subtype_id = msg_vals.get(
            'subtype_id') if msg_vals else msg_sudo.subtype_id.id
        # is it possible to have record but no subtype_id ?
        recipient_data = {
            'partners': [],
            'channels': [],
        }
        res = self.env['mail.followers']._get_recipient_data(
            self, message_type, subtype_id, pids, cids)
        # if not res:
        return recipient_data

        author_id = msg_vals.get('author_id') or message.author_id.id
        for pid, cid, active, pshare, ctype, notif, groups in res:
            # do not notify the author of its own messages
            if pid and pid == author_id and not self.env.context.get('mail_notify_author'):
                continue
            if pid:
                if active is False:
                    continue
                pdata = {'id': pid, 'active': active,
                         'share': pshare, 'groups': groups}
                if notif == 'inbox':
                    recipient_data['partners'].append(
                        dict(pdata, notif=notif, type='user'))
                elif not pshare and notif:  # has an user and is not shared, is therefore user
                    recipient_data['partners'].append(
                        dict(pdata, notif=notif, type='user'))
                elif pshare and notif:  # has an user but is shared, is therefore portal
                    recipient_data['partners'].append(
                        dict(pdata, notif=notif, type='portal'))
                else:  # has no user, is therefore customer
                    recipient_data['partners'].append(
                        dict(pdata, notif=notif if notif else 'email', type='customer'))
            elif cid:
                recipient_data['channels'].append(
                    {'id': cid, 'notif': notif, 'type': ctype})

        # add partner ids in email channels
        email_cids = [r['id']
                      for r in recipient_data['channels'] if r['notif'] == 'email']
        if email_cids:
            # we are doing a similar search in ocn_client
            # Could be interesting to make everything in a single query.
            # ocn_client: (searching all partners linked to channels of type chat).
            # here      : (searching all partners linked to channels with notif email if email is not the author one)
            # TDE FIXME: use email_sanitized
            email_from = msg_vals.get('email_from') or message.email_from
            exept_partner = [r['id'] for r in recipient_data['partners']]
            if author_id:
                exept_partner.append(author_id)
            new_pids = self.env['res.partner'].sudo().search([
                ('id', 'not in', exept_partner),
                ('channel_ids', 'in', email_cids),
                ('email', 'not in', [email_from]),
            ])
            for partner in new_pids:
                # caution: side effect, if user has notif type inbox, will receive en email anyway?
                # ocn_client: will add partners to recipient recipient_data. more ocn notifications. We neeed to filter them maybe
                recipient_data['partners'].append(
                    {'id': partner.id, 'share': True, 'active': True, 'notif': 'email', 'type': 'channel_email', 'groups': []})

        return recipient_data
