# -*- coding: utf-8 -*-
# from odoo import http


# class ClxCrm(http.Controller):
#     @http.route('/clx_crm/clx_crm/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/clx_crm/clx_crm/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('clx_crm.listing', {
#             'root': '/clx_crm/clx_crm',
#             'objects': http.request.env['clx_crm.clx_crm'].search([]),
#         })

#     @http.route('/clx_crm/clx_crm/objects/<model("clx_crm.clx_crm"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('clx_crm.object', {
#             'object': obj
#         })
