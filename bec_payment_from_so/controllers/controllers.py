# -*- coding: utf-8 -*-
from odoo import http

# class BecPaymentFromSo(http.Controller):
#     @http.route('/bec_payment_from_so/bec_payment_from_so/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bec_payment_from_so/bec_payment_from_so/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('bec_payment_from_so.listing', {
#             'root': '/bec_payment_from_so/bec_payment_from_so',
#             'objects': http.request.env['bec_payment_from_so.bec_payment_from_so'].search([]),
#         })

#     @http.route('/bec_payment_from_so/bec_payment_from_so/objects/<model("bec_payment_from_so.bec_payment_from_so"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bec_payment_from_so.object', {
#             'object': obj
#         })