# -*- coding: utf-8 -*-

from odoo import models, fields, api

class bec_invoice_AccountInvoice(models.Model):
    _inherit = "account.invoice"

    patient_id = fields.Many2one('res.partner', string='Patient', change_default=True,
        readonly=True, states={'draft': [('readonly', False)]}, domain="[('customer','=', True)]")


    # @api.multi
    # def assign_outstanding_credit(self, credit_aml_id):
    # 	print (credit_aml_id,'credit_aml_id')
    # 	exit()

#     _name = 'bec_invoice.bec_invoice'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100