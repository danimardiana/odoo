# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo.http import Controller, request, route


class RequestForm(Controller):

    @route(['/requestform'], type='http', auth="user", website=True)
    def request_form(self, **kw):
        main_task = request.env['main.task'].search([('req_type', '=', 'update')])
        values = {}
        for task in main_task:
            values.update({
                task.id: task.name
            })
        return request.render("clx_task_management.request_form_template", values)

    @route(['/addrequestline'], type='http', auth="user", website=True)
    def request_line(self, **kw):
        # values = self._prepare_home_portal_values()
        return request.render("clx_task_management.request_form_template")
