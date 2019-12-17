# -*- coding: utf-8 -*-
from odoo import http

# class BecTypeCoaSimrs(http.Controller):
#     @http.route('/bec_type_coa_simrs/bec_type_coa_simrs/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bec_type_coa_simrs/bec_type_coa_simrs/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('bec_type_coa_simrs.listing', {
#             'root': '/bec_type_coa_simrs/bec_type_coa_simrs',
#             'objects': http.request.env['bec_type_coa_simrs.bec_type_coa_simrs'].search([]),
#         })

#     @http.route('/bec_type_coa_simrs/bec_type_coa_simrs/objects/<model("bec_type_coa_simrs.bec_type_coa_simrs"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bec_type_coa_simrs.object', {
#             'object': obj
#         })