# -*- coding: utf-8 -*-
from odoo import http

# class BecIdSimrs(http.Controller):
#     @http.route('/bec_id_simrs/bec_id_simrs/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bec_id_simrs/bec_id_simrs/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('bec_id_simrs.listing', {
#             'root': '/bec_id_simrs/bec_id_simrs',
#             'objects': http.request.env['bec_id_simrs.bec_id_simrs'].search([]),
#         })

#     @http.route('/bec_id_simrs/bec_id_simrs/objects/<model("bec_id_simrs.bec_id_simrs"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bec_id_simrs.object', {
#             'object': obj
#         })