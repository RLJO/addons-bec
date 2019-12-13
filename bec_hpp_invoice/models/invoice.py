# -*- coding: utf-8 -*-

from odoo import models, fields, api

class bec_hpp_invoice_AccountInvoice(models.Model):
	_inherit = "account.invoice"

	account_hpp_id = fields.Many2one('account.move', string='Journal Entry Hpp',
        readonly=True, index=True, ondelete='restrict', copy=False,
        help="Link to the automatically generated Journal Items for hpp.")
