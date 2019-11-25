# -*- coding: utf-8 -*-
from odoo import http

# class BecInvoice(http.Controller):
#     @http.route('/bec_invoice/bec_invoice/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bec_invoice/bec_invoice/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('bec_invoice.listing', {
#             'root': '/bec_invoice/bec_invoice',
#             'objects': http.request.env['bec_invoice.bec_invoice'].search([]),
#         })

#     @http.route('/bec_invoice/bec_invoice/objects/<model("bec_invoice.bec_invoice"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bec_invoice.object', {
#             'object': obj
#         })