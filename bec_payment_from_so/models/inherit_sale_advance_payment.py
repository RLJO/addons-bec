# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class bec_SaleAdvancePayment(models.TransientModel):
    _inherit = "sale.advance.payment"

    @api.multi
    def make_advance_payment(self):
        sale_id = self.env.context.get('active_id', False)
        if sale_id:
            sale = self.env['sale.order'].browse(sale_id)

            exchange_rate = self.env['res.currency']._get_conversion_rate(sale.company_id.currency_id, sale.currency_id, sale.company_id, sale.date_order)
            currency_amount = self.amount_to_pay * (1.0 / exchange_rate)
            payment_dict = {   'payment_type': 'inbound',
                               'partner_id': sale.partner_id and sale.partner_id.id,
                               'partner_type': 'customer',
                               'journal_id': self.journal_id and self.journal_id.id,
                               'company_id': sale.company_id and sale.company_id.id,
                               'currency_id':sale.pricelist_id.currency_id.id,
                               'payment_date': sale.date_order,
                               'amount': currency_amount,
                               'sale_id': sale.id,
                               'name': _("Payment") + " - " + sale.name,
                               'communication': sale.name,
                               'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id
                          }
            payment = self.env['account.payment'].create(payment_dict)
            payment.post()

            confirm_sale = sale.action_confirm()
            create_invoice = sale.action_invoice_create()
            invoice = self.env['account.invoice'].browse(create_invoice)
            validate_invoice = invoice.action_invoice_open()
            # payment_invoice = invoice._compute_payments()
            # print('create invoice',create_invoice)
        return {'type': 'ir.actions.act_window_close'}
