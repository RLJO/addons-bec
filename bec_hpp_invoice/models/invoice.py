# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError, AccessError

class bec_hpp_invoice_AccountInvoice(models.Model):
	_inherit = "account.invoice"

	account_hpp_id = fields.Many2one('account.move', string='Journal Entry Hpp',
        readonly=True, index=True, ondelete='restrict', copy=False,
        help="Link to the automatically generated Journal Items for hpp.")

	account_hnr_dokter_id = fields.Many2one('account.move', string='Journal Entry Honor Dokter',
        readonly=True, index=True, ondelete='restrict', copy=False,
        help="Link to the automatically generated Journal Items for hpp.")

	active = fields.Boolean(default=True,string='Approval Cancel Invoice') #jika true maka invoice tidak bisa cancel via api


	@api.multi
	def action_cancel_via_service(self):
		if self.active == True:
			raise UserError(_('Invoice can`t be canceled'))
		else:
			# reverse journal entries invoice
			res_inv = self.env['account.move'].browse(self.move_id.id).reverse_moves(datetime.now())
			# print(self.move_id.id,'invoice')

			# reverse journal entries hpp invoice
			res_hpp_inv = self.env['account.move'].browse(self.account_hpp_id.id).reverse_moves(datetime.now())

			# reserver honor Dokter
			res_honor_dokter_inv = self.env['account.move'].browse(self.account_hnr_dokter_id.id).reverse_moves(datetime.now())
			
			# print(self.account_hpp_id.id,'hpp')
			for rec in self.payment_ids:
				for move in rec.move_line_ids.mapped('move_id'):
					# print(move.id,' move id')
					if len(str(move.id)) > 0:
						res_move = self.env['account.move'].browse(move.id).reverse_moves(datetime.now())
						rec.state = 'cancelled'


			moves = self.env['account.move']
			for inv in self:
				if inv.move_id:
					moves += inv.move_id
				#unreconcile all journal items of the invoice, since the cancellation will unlink them anyway
				inv.move_id.line_ids.filtered(lambda x: x.account_id.reconcile).remove_move_reconcile()
			# First, set the invoices as cancelled and detach the move ids
			self.write({'state': 'cancel', 'move_id': False})
