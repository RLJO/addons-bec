# -*- coding: utf-8 -*-
from odoo import http

# class BecHppInvoice(http.Controller):
#     @http.route('/bec_hpp_invoice/bec_hpp_invoice/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bec_hpp_invoice/bec_hpp_invoice/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('bec_hpp_invoice.listing', {
#             'root': '/bec_hpp_invoice/bec_hpp_invoice',
#             'objects': http.request.env['bec_hpp_invoice.bec_hpp_invoice'].search([]),
#         })

#     @http.route('/bec_hpp_invoice/bec_hpp_invoice/objects/<model("bec_hpp_invoice.bec_hpp_invoice"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bec_hpp_invoice.object', {
#             'object': obj
#         })