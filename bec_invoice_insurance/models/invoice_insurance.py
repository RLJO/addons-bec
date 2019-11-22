# -*- coding: utf-8 -*-

from odoo import models, fields, api

class bec_invoice_insurance(models.Model):
    _name = 'invoice.insurance'
    _inherit = ['mail.thread']

    name = fields.Char('No Invoice Insurance', required=True, index=True, copy=False, default='New')
    partner_id = fields.Many2one('res.partner', string='Customer',required=True, domain="[('customer','=',True)]")
    state = fields.Selection([
	        ('draft', 'Draft'),
	        ('done', 'Done'),
	        ('cancel', 'Cancelled'),
	    	], string='state',default='draft',
	        copy=False, index=True, store=True
	       )
    line_ids = fields.One2many('invoice.insurance.line', 'inv_insurance_id','Invoice',readonly=False,copy=True)

    # @api.model
    # def create(self, vals):
    #     if vals.get('name', 'New') == 'New':
    #         vals['name'] = self.env['ir.sequence'].next_by_code('invoice.insurance') or '-'
    #     return super(bec_invoice_insurance, self).create(vals)

    @api.multi
    def button_confirm(self):
    	if self.name == 'New':
    		self.name = self.env['ir.sequence'].next_by_code('invoice.insurance') or '-'
    	return self.write({'state': 'done'})

    @api.multi
    def button_cancel(self):
    	return self.write({'state': 'cancel'})

    @api.multi
    def button_draft(self):
    	return self.write({'state': 'draft'})

# class bec_invoice_AccountInvoice(models.Model):
#     _inherit = "account.invoice"

#     inv_insurance_id = fields.Many2one('invoice.insurance', string='Invoice Insurance',
#         ondelete='cascade', index=True)


class bec_invoice_insurance_line(models.Model):
    _name = 'invoice.insurance.line'

    # def _compute_partner(self):
    # 	print('eeeee')

    inv_insurance_id = fields.Many2one('invoice.insurance', string='Invoice Insurance',
        ondelete='cascade', index=True)
    partner_id_order = fields.Many2one('res.partner', string='Customer', domain="[('customer','=',True)]", required=True)

    # name = fields.Many2one('account.invoice', string='Invoice',
    #     ondelete='cascade', index=True,domain="['&',('type','=','out_invoice'),('state','not in',['draft','cancel'])]")
    name = fields.Many2one('account.invoice', string='Invoice',
        ondelete='cascade', index=True,domain="[('type','=','out_invoice')]", required=True)
    partner_id = fields.Many2one('res.partner', string='Customer', related="name.partner_id")
    amount_total = fields.Monetary(string='Total',
        store=True, related="name.amount_total")
    residual = fields.Monetary(string='Amount Due',
        store=True, related="name.residual")
    currency_id = fields.Many2one('res.currency', string='Currency',
        required=True, readonly=True,related="name.currency_id")

    state = fields.Selection([
            ('draft','Draft'),
            ('open', 'Open'),
            ('in_payment', 'In Payment'),
            ('paid', 'Paid'),
            ('cancel', 'Cancelled'),
        ], string='Status', index=True, readonly=True, related="name.state")


    @api.onchange('partner_id_order')
    def _invoice_with_partner(self):
    	print('ddd')

    	print(self.partner_id_order,' mmm')
    	domain_asset = [('partner_id', '=',int(self.partner_id_order))]
    	return {'domain': {'name': domain_asset}}

    