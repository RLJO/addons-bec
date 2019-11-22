# -*- coding: utf-8 -*-
from odoo import http

# class BecInvoiceInsurance(http.Controller):
#     @http.route('/bec_invoice_insurance/bec_invoice_insurance/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bec_invoice_insurance/bec_invoice_insurance/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('bec_invoice_insurance.listing', {
#             'root': '/bec_invoice_insurance/bec_invoice_insurance',
#             'objects': http.request.env['bec_invoice_insurance.bec_invoice_insurance'].search([]),
#         })

#     @http.route('/bec_invoice_insurance/bec_invoice_insurance/objects/<model("bec_invoice_insurance.bec_invoice_insurance"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bec_invoice_insurance.object', {
#             'object': obj
#         })