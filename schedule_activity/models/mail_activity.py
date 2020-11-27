# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.http import request
import datetime


class MailActivity(models.Model):
    """ Inherited Mail Acitvity to add custom field"""
    _inherit = 'mail.activity'
    supervisor_id = fields.Many2one('res.users', string="Supervisor")


class ActivityDashboard(models.Model):
    _name = 'activity.details'
    _description = 'Activity Dashboard'

    @api.model
    def get_activity_info(self):
        uid = request.session.uid
        cr = self.env.cr
        user_id = self.env['res.users'].browse(uid)
        today_date = datetime.datetime.now().date()
        todays_acitvities_count = self.env['mail.activity'].sudo().search_count(
            [('user_id', '=', uid), ('date_deadline', '=', today_date)])
        upcoming_acitvities_count = self.env['mail.activity'].sudo().search_count(
            [('user_id', '=', uid), ('date_deadline', '>', today_date)])
        late_acitvities_count = self.env['mail.activity'].sudo().search_count(
            [('user_id', '=', uid), ('date_deadline', '<', today_date)])

        user = self.env['res.users'].browse(uid)
        if user and (user.has_group('schedule_activity.group_activity_manager') or user.has_group('base.group_system')):
            team_ids = self.env['crm.team'].search([])
            member_ids = team_ids.mapped('member_ids').ids
            member_ids.extend(team_ids.mapped('user_id').ids)
            member_ids.append(user_id.id)
            acitvities_ids = self.env['mail.activity'].sudo().search([('user_id', 'in', member_ids)])
        elif user and user.has_group('schedule_activity.group_activity_supervisor'):
            member_ids = self.env['crm.team'].search([('user_id', '=', uid)]).member_ids.ids
            member_ids.append(uid)
            acitvities_ids = self.env['mail.activity'].sudo().search([('user_id', 'in', member_ids)], limit=10)
        else:
            acitvities_ids = self.env['mail.activity'].sudo().search([('user_id', '=', uid)], limit=10)

        activity_details = []
        activity_details.append({
            'todays_acitvities_count': todays_acitvities_count,
            'upcoming_acitvities_count': upcoming_acitvities_count,
            'overdue_acitvities_count': late_acitvities_count,
        })
        acitvities_ids = acitvities_ids.filtered(lambda x: x.user_id.id == user.id)
        if acitvities_ids:
            for record in acitvities_ids:
                if record.date_deadline == today_date:
                    activity_details.append({
                        'todays_activities_id': record.id,
                        'todays_activities_name': record.res_name,
                        'type': record.activity_type_id.name,
                        'assigned_to': record.user_id.name,
                        'supervisor': record.supervisor_id.name or "No Supervisor Assigned",
                        'date_deadline': record.date_deadline,
                    })

                elif record.date_deadline > today_date:
                    activity_details.append({
                        'upcoming_activities_id': record.id,
                        'upcoming_activities_name': record.res_name,
                        'type': record.activity_type_id.name,
                        'assigned_to': record.user_id.name,
                        'supervisor': record.supervisor_id.name or "No Supervisor Assigned",
                        'date_deadline': record.date_deadline,
                    })
                else:
                    activity_details.append({
                        'overdue_activities_id': record.id,
                        'overdue_activities_name': record.res_name,
                        'type': record.activity_type_id.name,
                        'assigned_to': record.user_id.name,
                        'supervisor': record.supervisor_id.name or "No Supervisor Assigned",
                        'date_deadline': record.date_deadline,
                    })

        return activity_details
