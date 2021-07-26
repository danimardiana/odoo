# -*- coding: utf-8 -*-
# from odoo import http


# class ClxUtils(http.Controller):
#     @http.route('/clx_utils/clx_utils/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/clx_utils/clx_utils/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('clx_utils.listing', {
#             'root': '/clx_utils/clx_utils',
#             'objects': http.request.env['clx_utils.clx_utils'].search([]),
#         })

#     @http.route('/clx_utils/clx_utils/objects/<model("clx_utils.clx_utils"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('clx_utils.object', {
#             'object': obj
#         })
