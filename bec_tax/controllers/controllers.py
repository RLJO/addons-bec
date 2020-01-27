# -*- coding: utf-8 -*-
from odoo import http

# class BecTax(http.Controller):
#     @http.route('/bec_tax/bec_tax/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bec_tax/bec_tax/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('bec_tax.listing', {
#             'root': '/bec_tax/bec_tax',
#             'objects': http.request.env['bec_tax.bec_tax'].search([]),
#         })

#     @http.route('/bec_tax/bec_tax/objects/<model("bec_tax.bec_tax"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bec_tax.object', {
#             'object': obj
#         })