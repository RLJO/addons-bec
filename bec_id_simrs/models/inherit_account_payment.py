# -*- coding: utf-8 -*-

import json
import re
import uuid
from functools import partial

from lxml import etree
from dateutil.relativedelta import relativedelta
from werkzeug.urls import url_encode

from odoo import api, exceptions, fields, models, _
from odoo.tools import email_re, email_split, email_escape_char, float_is_zero, float_compare, \
    pycompat, date_utils
from odoo.tools.misc import formatLang

from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning

from odoo.addons import decimal_precision as dp
import logging

class bec_account_payment(models.Model):
    _inherit = "account.payment"

    id_simrs = fields.Char(string='Id SIMRS')
    patient_id = fields.Many2one('res.partner', string='Patient')
    no_setoran_simrs = fields.Char(string='No Setoran SIMRS')

    payment_type = fields.Selection(selection_add=[('repayment_ar', 'Customer Repayment')])

    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        if not self.invoice_ids:
            # Set default partner type for the payment type
            if self.payment_type == 'inbound':
                self.partner_type = 'customer'
            elif self.payment_type == 'outbound':
                self.partner_type = 'supplier'
            elif self.payment_type == 'repayment_ar':
                self.partner_type = 'customer'
            else:
                self.partner_type = False
        # Set payment method domain
        res = self._onchange_journal()
        if not res.get('domain', {}):
            res['domain'] = {}
        jrnl_filters = self._compute_journal_domain_and_types()
        journal_types = jrnl_filters['journal_types']
        journal_types.update(['bank', 'cash'])
        res['domain']['journal_id'] = jrnl_filters['domain'] + [('type', 'in', list(journal_types))]
        return res

    @api.one
    @api.depends('invoice_ids', 'payment_type', 'partner_type', 'partner_id')
    def _compute_destination_account_id(self):
        # print('kkkkkkkk')
        if self.invoice_ids:
            self.destination_account_id = self.invoice_ids[0].account_id.id
        elif self.payment_type == 'transfer':
            if not self.company_id.transfer_account_id.id:
                raise UserError(_('There is no Transfer Account defined in the accounting settings. Please define one to be able to confirm this transfer.'))
            self.destination_account_id = self.company_id.transfer_account_id.id
        elif self.partner_id:
            if self.partner_type == 'customer':
                if self.payment_type == 'repayment_ar':
                    self.destination_account_id = self.partner_id.account_repayment_id.id
                else:
                    self.destination_account_id = self.partner_id.property_account_receivable_id.id
            else:
                self.destination_account_id = self.partner_id.property_account_payable_id.id
        elif self.partner_type == 'customer':
            default_account = self.env['ir.property'].get('property_account_receivable_id', 'res.partner')
            self.destination_account_id = default_account.id
        elif self.partner_type == 'supplier':
            default_account = self.env['ir.property'].get('property_account_payable_id', 'res.partner')
            self.destination_account_id = default_account.id

        # print(self.destination_account_id,' self.destination_account_id')


    @api.multi
    def post(self):
        """ Create the journal items for the payment and update the payment's state to 'posted'.
            A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
            and another in the destination reconcilable account (see _compute_destination_account_id).
            If invoice_ids is not empty, there will be one reconcilable move line per invoice to reconcile with.
            If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
        """
        for rec in self:

            if rec.state != 'draft':
                raise UserError(_("Only a draft payment can be posted."))

            if any(inv.state != 'open' for inv in rec.invoice_ids):
                raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

            # keep the name in case of a payment reset to draft
            if not rec.name:
                # Use the right sequence to set the name
                if rec.payment_type == 'transfer':
                    sequence_code = 'account.payment.transfer'
                else:
                    if rec.partner_type == 'customer':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.customer.invoice'
                        if rec.payment_type == 'repayment_ar':
                            sequence_code = 'account.repayment.customer.invoice'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.customer.refund'
                    if rec.partner_type == 'supplier':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.supplier.refund'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.supplier.invoice'
                rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.payment_date).next_by_code(sequence_code)
                if not rec.name and rec.payment_type != 'transfer':
                    raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))

            # Create the journal entry
            amount = rec.amount * (rec.payment_type in ('outbound', 'transfer') and 1 or -1)

            # print(amount,' amount')
            # exit()

            move = rec._create_payment_entry(amount)

            # In case of a transfer, the first journal entry created debited the source liquidity account and credited
            # the transfer account. Now we debit the transfer account and credit the destination liquidity account.
            if rec.payment_type == 'transfer':
                transfer_credit_aml = move.line_ids.filtered(lambda r: r.account_id == rec.company_id.transfer_account_id)
                transfer_debit_aml = rec._create_transfer_entry(amount)
                (transfer_credit_aml + transfer_debit_aml).reconcile()

            rec.write({'state': 'posted', 'move_name': move.name})
        return True

    def _get_shared_move_line_vals(self, debit, credit, amount_currency, move_id, invoice_id=False):
        """ Returns values common to both move lines (except for debit, credit and amount_currency which are reversed)
        """
        return {
            'partner_id': self.payment_type in ('inbound', 'outbound', 'repayment_ar') and self.env['res.partner']._find_accounting_partner(self.partner_id).id or False,
            'invoice_id': invoice_id and invoice_id.id or False,
            'move_id': move_id,
            'debit': debit,
            'credit': credit,
            'amount_currency': amount_currency or False,
            'payment_id': self.id,
            'journal_id': self.journal_id.id,
        }

    # def _create_payment_entry(self, amount):
    #     """ Create a journal entry corresponding to a payment, if the payment references invoice(s) they are reconciled.
    #         Return the journal entry.
    #     """
    #     aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
    #     debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amount, self.currency_id, self.company_id.currency_id)

    #     move = self.env['account.move'].create(self._get_move_vals())

    #     #Write line corresponding to invoice payment
    #     counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
    #     counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.invoice_ids))
    #     counterpart_aml_dict.update({'currency_id': currency_id})

    #     print(counterpart_aml_dict,' counterpart_aml_dict')
    #     counterpart_aml = aml_obj.create(counterpart_aml_dict)

    #     #Reconcile with the invoices
    #     if self.payment_difference_handling == 'reconcile' and self.payment_difference:
    #         writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
    #         debit_wo, credit_wo, amount_currency_wo, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(self.payment_difference, self.currency_id, self.company_id.currency_id)
    #         writeoff_line['name'] = self.writeoff_label
    #         writeoff_line['account_id'] = self.writeoff_account_id.id
    #         writeoff_line['debit'] = debit_wo
    #         writeoff_line['credit'] = credit_wo
    #         writeoff_line['amount_currency'] = amount_currency_wo
    #         writeoff_line['currency_id'] = currency_id
    #         writeoff_line = aml_obj.create(writeoff_line)
    #         if counterpart_aml['debit'] or (writeoff_line['credit'] and not counterpart_aml['credit']):
    #             counterpart_aml['debit'] += credit_wo - debit_wo
    #         if counterpart_aml['credit'] or (writeoff_line['debit'] and not counterpart_aml['debit']):
    #             counterpart_aml['credit'] += debit_wo - credit_wo
    #         counterpart_aml['amount_currency'] -= amount_currency_wo

    #     #Write counterpart lines
    #     if not self.currency_id.is_zero(self.amount):
    #         if not self.currency_id != self.company_id.currency_id:
    #             amount_currency = 0
    #         liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
    #         liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
    #         aml_obj.create(liquidity_aml_dict)

    #     #validate the payment
    #     if not self.journal_id.post_at_bank_rec:
    #         move.post()

    #     #reconcile the invoice receivable/payable line(s) with the payment
    #     if self.invoice_ids:
    #         self.invoice_ids.register_payment(counterpart_aml)

    #     return move



class bec_AccountInvoice(models.Model):
    _inherit = "account.invoice"

    id_simrs = fields.Char(string='Id SIMRS')
    kd_t_simrs = fields.Char(string='Kode T SIMRS')
    no_inv_simrs = fields.Char(string='No Invoice SIMRS')
    no_tagihan_simrs = fields.Char(string='No Tagihan SIMRS')

    no_bapb_simrs = fields.Char(string='Nomor BAPB')
    no_faktur_simrs = fields.Char(string='Nomor Faktur')
    no_po_simrs = fields.Char(string='Nomor PO')

    nm_kasir = fields.Char(string='Nama Kasir')
    shift_kasir = fields.Char(string='Shift Kasir')

    account_repayment_id = fields.Many2one('account.account', string='Account repayment',
        readonly=True, states={'draft': [('readonly', False)]},
        domain=[('deprecated', '=', False),('internal_type','=','receivable')], help="The partner account used for this invoice.")

    # @api.multi
    # def assign_outstanding_credit(self, credit_aml_id):
    #     self.ensure_one()

    #     credit_aml = self.env['account.move.line'].browse(credit_aml_id)
    #     print(credit_aml,' credit_aml')
        

    #     if not credit_aml.currency_id and self.currency_id != self.company_id.currency_id:
    #         amount_currency = self.company_id.currency_id._convert(credit_aml.balance, self.currency_id, self.company_id, credit_aml.date or fields.Date.today())
    #         credit_aml.with_context(allow_amount_currency=True, check_move_validity=False).write({
    #             'amount_currency': amount_currency,
    #             'currency_id': self.currency_id.id})
            

        
    #     if credit_aml.payment_id:
    #         print('masuk')
    #         # exit()
    #         credit_aml.payment_id.write({'invoice_ids': [(4, self.id, None)]})

    #     # exit()
    #     return self.register_payment(credit_aml)


    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        account_id = False
        payment_term_id = False
        fiscal_position = False
        bank_id = False
        warning = {}
        domain = {}
        company_id = self.company_id.id
        p = self.partner_id if not company_id else self.partner_id.with_context(force_company=company_id)
        type = self.type
        if p:
            rec_account = p.property_account_receivable_id
            pay_account = p.property_account_payable_id
            if not rec_account and not pay_account:
                action = self.env.ref('account.action_account_config')
                msg = _('Cannot find a chart of accounts for this company, You should configure it. \nPlease go to Account Configuration.')
                raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))

            if type in ('in_invoice', 'in_refund'):
                account_id = pay_account.id
                payment_term_id = p.property_supplier_payment_term_id.id
            else:
                account_id = rec_account.id
                payment_term_id = p.property_payment_term_id.id

            delivery_partner_id = self.get_delivery_partner_id()
            fiscal_position = self.env['account.fiscal.position'].get_fiscal_position(self.partner_id.id, delivery_id=delivery_partner_id)

            # If partner has no warning, check its company
            if p.invoice_warn == 'no-message' and p.parent_id:
                p = p.parent_id
            if p.invoice_warn and p.invoice_warn != 'no-message':
                # Block if partner only has warning but parent company is blocked
                if p.invoice_warn != 'block' and p.parent_id and p.parent_id.invoice_warn == 'block':
                    p = p.parent_id
                warning = {
                    'title': _("Warning for %s") % p.name,
                    'message': p.invoice_warn_msg
                    }
                if p.invoice_warn == 'block':
                    self.partner_id = False

        self.account_id = account_id

        # print(p.account_repayment_id)
        # print(p)
        self.account_repayment_id = p.account_repayment_id
        self.payment_term_id = payment_term_id
        self.date_due = False
        self.fiscal_position_id = fiscal_position

        if type in ('in_invoice', 'out_refund'):
            bank_ids = p.commercial_partner_id.bank_ids
            bank_id = bank_ids[0].id if bank_ids else False
            self.partner_bank_id = bank_id
            domain = {'partner_bank_id': [('id', 'in', bank_ids.ids)]}

        res = {}
        if warning:
            res['warning'] = warning
        if domain:
            res['domain'] = domain
        return res

    @api.multi
    def action_move_create(self):
        # print('action_move_create')
        """ Creates invoice related analytics and financial move lines """
        account_move = self.env['account.move']

        for inv in self:
            if not inv.journal_id.sequence_id:
                raise UserError(_('Please define sequence on the journal related to this invoice.'))
            if not inv.invoice_line_ids.filtered(lambda line: line.account_id):
                raise UserError(_('Please add at least one invoice line.'))
            if inv.move_id:
                continue


            if not inv.date_invoice:
                inv.write({'date_invoice': fields.Date.context_today(self)})
            if not inv.date_due:
                inv.write({'date_due': inv.date_invoice})
            company_currency = inv.company_id.currency_id

            # create move lines (one per invoice line + eventual taxes and analytic lines)
            iml = inv.invoice_line_move_line_get()
            iml += inv.tax_line_move_line_get()

            diff_currency = inv.currency_id != company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total, total_currency, iml = inv.compute_invoice_totals(company_currency, iml)

            name = inv.name or ''
            if inv.payment_term_id:
                # print('satu')
                if self.partner_id.id == self.company_id.penjamin_id.id and len(self.account_repayment_id) > 0:
                    # print('dua')
                    # print(self.payment_ids,' payment_ids')

                    domain_payment = [('id_simrs', '!=', False),('id_simrs', '=', self.id_simrs),('partner_id', '=', int(self.partner_id))]
                    payment_dp = self.env['account.payment'].search(domain_payment)
                    payment_amount = 0
                    for payment in self.payment_ids:
                    # for payment in payment_dp:
                        payment_amount = payment_amount+payment.amount

                    # jika tidak ada dp
                    if len(self.payment_ids) <= 0:
                        # print('tiga')
                        iml.append({
                            'type': 'dest',
                            'name': name,
                            'price': total,
                            'account_id': inv.account_repayment_id.id,
                            'date_maturity': inv.date_due,
                            'amount_currency': diff_currency and total_currency,
                            'currency_id': diff_currency and inv.currency_id.id,
                            'invoice_id': inv.id
                        })
                        # residual = total
                    # jika ada dp
                    else:
                        if total <= payment_amount:
                            # print('empat')
                            # print('langsung proses odoo default')
                            iml.append({
                                'type': 'dest',
                                'name': name,
                                'price': total,
                                'account_id': inv.account_id.id,
                                'date_maturity': inv.date_due,
                                'amount_currency': diff_currency and total_currency,
                                'currency_id': diff_currency and inv.currency_id.id,
                                'invoice_id': inv.id
                            })
                            # residual = total
                        else:
                            # print('lima')
                            # print('proses dg coa penampung deposit')
                            amount_repayment = total-payment_amount
                            #jurnal deposit pasien
                            iml.append({
                                'type': 'dest',
                                'name': name,
                                'price': payment_amount,
                                'account_id': inv.account_id.id,
                                'date_maturity': inv.date_due,
                                'amount_currency': diff_currency and total_currency,
                                'currency_id': diff_currency and inv.currency_id.id,
                                'invoice_id': inv.id
                            })

                            #jurnal repayment
                            iml.append({
                                'type': 'dest',
                                'name': name,
                                'price': amount_repayment,
                                'account_id': inv.account_repayment_id.id,
                                'date_maturity': inv.date_due,
                                'amount_currency': diff_currency and total_currency,
                                'currency_id': diff_currency and inv.currency_id.id,
                                'invoice_id': inv.id
                            })
                            # residual = amount_repayment

                else:
                    totlines = inv.payment_term_id.with_context(currency_id=company_currency.id).compute(total, inv.date_invoice)[0]
                    res_amount_currency = total_currency
                    for i, t in enumerate(totlines):
                        if inv.currency_id != company_currency:
                            amount_currency = company_currency._convert(t[1], inv.currency_id, inv.company_id, inv._get_currency_rate_date() or fields.Date.today())
                        else:
                            amount_currency = False

                        # last line: add the diff
                        res_amount_currency -= amount_currency or 0
                        if i + 1 == len(totlines):
                            amount_currency += res_amount_currency

                        iml.append({
                            'type': 'dest',
                            'name': name,
                            'price': t[1],
                            'account_id': inv.account_id.id,
                            'date_maturity': t[0],
                            'amount_currency': diff_currency and amount_currency,
                            'currency_id': diff_currency and inv.currency_id.id,
                            'invoice_id': inv.id
                        })
            else:
                # yang input jurnal deposit debit

                residual = 0

                if self.partner_id.id == self.company_id.penjamin_id.id and len(self.account_repayment_id) > 0:
                    # print('dua')
                    # print(self.payment_ids,' payment_ids')

                    domain_payment = [('id_simrs', '!=', False),('id_simrs', '=', self.id_simrs),('partner_id', '=', int(self.partner_id))]
                    payment_dp = self.env['account.payment'].search(domain_payment)
                    payment_amount = 0
                    for payment in self.payment_ids:
                    # for payment in payment_dp:
                        payment_amount = payment_amount+payment.amount

                    # jika tidak ada dp
                    if len(self.payment_ids) <= 0:
                        # print('tiga')
                        iml.append({
                            'type': 'dest',
                            'name': name,
                            'price': total,
                            'account_id': inv.account_repayment_id.id,
                            'date_maturity': inv.date_due,
                            'amount_currency': diff_currency and total_currency,
                            'currency_id': diff_currency and inv.currency_id.id,
                            'invoice_id': inv.id
                        })
                        # residual = total
                    # jika ada dp
                    else:
                        if total <= payment_amount:
                            # print('empat')
                            # print('langsung proses odoo default')
                            iml.append({
                                'type': 'dest',
                                'name': name,
                                'price': total,
                                'account_id': inv.account_id.id,
                                'date_maturity': inv.date_due,
                                'amount_currency': diff_currency and total_currency,
                                'currency_id': diff_currency and inv.currency_id.id,
                                'invoice_id': inv.id
                            })
                            # residual = total
                        else:
                            # print('lima')
                            # print('proses dg coa penampung deposit')
                            amount_repayment = total-payment_amount
                            #jurnal deposit pasien
                            iml.append({
                                'type': 'dest',
                                'name': name,
                                'price': payment_amount,
                                'account_id': inv.account_id.id,
                                'date_maturity': inv.date_due,
                                'amount_currency': diff_currency and total_currency,
                                'currency_id': diff_currency and inv.currency_id.id,
                                'invoice_id': inv.id
                            })

                            #jurnal repayment
                            iml.append({
                                'type': 'dest',
                                'name': name,
                                'price': amount_repayment,
                                'account_id': inv.account_repayment_id.id,
                                'date_maturity': inv.date_due,
                                'amount_currency': diff_currency and total_currency,
                                'currency_id': diff_currency and inv.currency_id.id,
                                'invoice_id': inv.id
                            })
                            # residual = amount_repayment

                else:
                    # print('enam')
                    # print('jurnal pelunasan belum ada')
                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': total,
                        'account_id': inv.account_id.id,
                        'date_maturity': inv.date_due,
                        'amount_currency': diff_currency and total_currency,
                        'currency_id': diff_currency and inv.currency_id.id,
                        'invoice_id': inv.id
                    })
                    # residual = total

            part = self.env['res.partner']._find_accounting_partner(inv.partner_id)
            line = [(0, 0, self.line_get_convert(l, part.id)) for l in iml]
            line = inv.group_lines(iml, line)
            line = inv.finalize_invoice_move_lines(line)

            date = inv.date or inv.date_invoice
            move_vals = {
                'ref': inv.reference,
                'line_ids': line,
                'journal_id': inv.journal_id.id,
                'date': date,
                'narration': inv.comment,
            }

            move = account_move.create(move_vals)
            # Pass invoice in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:
            move.post(invoice = inv)
            # make the invoice point to that move
            vals = {
                'move_id': move.id,
                'date': date,
                'move_name': move.name,
            }

            inv.write(vals)
        return True


    @api.one
    @api.depends(
        'state', 'currency_id', 'invoice_line_ids.price_subtotal',
        'move_id.line_ids.amount_residual',
        'move_id.line_ids.currency_id')
    def _compute_residual(self):
        # print('testttt')
        residual = 0.0
        residual_company_signed = 0.0
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        for line in self.sudo().move_id.line_ids:

            # if line.account_id == self.account_repayment_id and len(self.account_repayment_id) > 0 and self.partner_id.id == self.company_id.penjamin_id.id:
            if self.partner_id.id == self.company_id.penjamin_id.id and len(self.account_repayment_id) > 0:
                if line.account_id == self.account_repayment_id:
                    residual_company_signed += line.amount_residual
                    if line.currency_id == self.currency_id:
                        residual += line.amount_residual_currency if line.currency_id else line.amount_residual
                    else:
                        from_currency = line.currency_id or line.company_id.currency_id
                        residual += from_currency._convert(line.amount_residual, self.currency_id, line.company_id, line.date or fields.Date.today())
            else:
                print('residu masuk 2')
                if line.account_id == self.account_id:
                    residual_company_signed += line.amount_residual
                    if line.currency_id == self.currency_id:
                        residual += line.amount_residual_currency if line.currency_id else line.amount_residual
                    else:
                        from_currency = line.currency_id or line.company_id.currency_id
                        residual += from_currency._convert(line.amount_residual, self.currency_id, line.company_id, line.date or fields.Date.today())
        self.residual_company_signed = abs(residual_company_signed) * sign
        self.residual_signed = abs(residual) * sign
        self.residual = abs(residual)

        # print(residual,' residu')

        digits_rounding_precision = self.currency_id.rounding
        if float_is_zero(self.residual, precision_rounding=digits_rounding_precision):
            self.reconciled = True
        else:
            self.reconciled = False


    @api.one
    def _get_outstanding_info_JSON(self):
        self.outstanding_credits_debits_widget = json.dumps(False)
        if self.state == 'open':
            domain_payment = [('id_simrs', '!=', False),('id_simrs', '=', self.id_simrs),('partner_id', '=', self.env['res.partner']._find_accounting_partner(self.partner_id).id)]
            payment_dp = self.env['account.payment'].search(domain_payment)

            # payment_ids=[]
            # for d in payment_dp:
            #     payment_ids.append(d.id)

            if self.partner_id.id == self.company_id.penjamin_id.id: #jika penjamin umum
                # domain = [('account_id', '=', self.account_id.id),
                #           ('partner_id', '=', self.env['res.partner']._find_accounting_partner(self.partner_id).id),
                #           ('reconciled', '=', False),
                #           '|',
                #             '&', ('amount_residual_currency', '!=', 0.0), ('currency_id','!=', None),
                #             '&', ('amount_residual_currency', '=', 0.0), '&', ('currency_id','=', None), ('amount_residual', '!=', 0.0)
                #             ,('payment_id', 'in', self.payment_ids.ids)]

                domain = [('account_id', 'in', [self.account_id.id,self.account_repayment_id.id]),
                          ('partner_id', '=', self.env['res.partner']._find_accounting_partner(self.partner_id).id),
                          ('reconciled', '=', False),
                          '|',
                            '&', ('amount_residual_currency', '!=', 0.0), ('currency_id','!=', None),
                            '&', ('amount_residual_currency', '=', 0.0), '&', ('currency_id','=', None), ('amount_residual', '!=', 0.0)
                            ,('payment_id', 'in', payment_dp.ids)]
            else:
                domain = [('account_id', '=', self.account_id.id),
                          ('partner_id', '=', self.env['res.partner']._find_accounting_partner(self.partner_id).id),
                          ('reconciled', '=', False),
                          '|',
                            '&', ('amount_residual_currency', '!=', 0.0), ('currency_id','!=', None),
                            '&', ('amount_residual_currency', '=', 0.0), '&', ('currency_id','=', None), ('amount_residual', '!=', 0.0)]


            # domain = [('account_id', '=', self.account_id.id),
            #               ('partner_id', '=', self.env['res.partner']._find_accounting_partner(self.partner_id).id),
            #               ('reconciled', '=', False),
            #               '|',
            #                 '&', ('amount_residual_currency', '!=', 0.0), ('currency_id','!=', None),
            #                 '&', ('amount_residual_currency', '=', 0.0), '&', ('currency_id','=', None), ('amount_residual', '!=', 0.0)
            #                 ]


            if self.type in ('out_invoice', 'in_refund'):
                domain.extend([('credit', '>', 0), ('debit', '=', 0)])
                type_payment = _('Outstanding credits')
            else:
                domain.extend([('credit', '=', 0), ('debit', '>', 0)])
                type_payment = _('Outstanding debits')

            # print(domain,' domain')
            info = {'title': '', 'outstanding': True, 'content': [], 'invoice_id': self.id}
            lines = self.env['account.move.line'].search(domain)

            # print(lines,' lines')

            currency_id = self.currency_id
            if len(lines) != 0:
                for line in lines:
                    # get the outstanding residual value in invoice currency
                    if line.currency_id and line.currency_id == self.currency_id:
                        amount_to_show = abs(line.amount_residual_currency)
                    else:
                        currency = line.company_id.currency_id
                        amount_to_show = currency._convert(abs(line.amount_residual), self.currency_id, self.company_id, line.date or fields.Date.today())
                    if float_is_zero(amount_to_show, precision_rounding=self.currency_id.rounding):
                        continue
                    if line.ref :
                        title = '%s : %s' % (line.move_id.name, line.ref)
                    else:
                        title = line.move_id.name
                    info['content'].append({
                        'journal_name': line.ref or line.move_id.name,
                        'title': title,
                        'amount': amount_to_show,
                        'currency': currency_id.symbol,
                        'id': line.id,
                        'position': currency_id.position,
                        'digits': [69, self.currency_id.decimal_places],
                    })
                info['title'] = type_payment
                self.outstanding_credits_debits_widget = json.dumps(info)
                self.has_outstanding = True




class bec_Partner(models.Model):
    _inherit = "res.partner"

    id_simrs = fields.Char(string='Id Customer SIMRS')
    account_repayment_id = fields.Many2one('account.account', string='Account repayment',
        domain=[('deprecated', '=', False),('internal_type','=','receivable')])

class bec_AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    id_simrs = fields.Char(string='Id refund dp SIMRS')

class bec_product(models.Model):
    _inherit = "product.product"

    id_simrs = fields.Char(string='Id product SIMRS')

class bec_account_account(models.Model):
    _inherit = "account.account"

    id_simrs = fields.Char(string='Id COA SIMRS')


class bec_account_ResCompany(models.Model):
    _inherit = 'res.company'
    penjamin_id = fields.Many2one('res.partner', string="Penjamin Umum",domain="[('customer', '=', True)]", readonly=False)

class bec_AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # @api.multi
    # def reconcile(self, writeoff_acc_id=False, writeoff_journal_id=False):

    #     print(writeoff_acc_id,' writeoff_acc_id')
    #     print(writeoff_journal_id,' writeoff_journal_id')
    #     # Empty self can happen if the user tries to reconcile entries which are already reconciled.
    #     # The calling method might have filtered out reconciled lines.
    #     if not self:
    #         return True

    #     self._check_reconcile_validity()
    #     #reconcile everything that can be
    #     remaining_moves = self.auto_reconcile_lines()

    #     writeoff_to_reconcile = self.env['account.move.line']
    #     #if writeoff_acc_id specified, then create write-off move with value the remaining amount from move in self
    #     if writeoff_acc_id and writeoff_journal_id and remaining_moves:
    #         all_aml_share_same_currency = all([x.currency_id == self[0].currency_id for x in self])
    #         writeoff_vals = {
    #             'account_id': writeoff_acc_id.id,
    #             'journal_id': writeoff_journal_id.id
    #         }
    #         if not all_aml_share_same_currency:
    #             writeoff_vals['amount_currency'] = False
    #         writeoff_to_reconcile = remaining_moves._create_writeoff([writeoff_vals])
    #         #add writeoff line to reconcile algorithm and finish the reconciliation
    #         remaining_moves = (remaining_moves + writeoff_to_reconcile).auto_reconcile_lines()
    #     # Check if reconciliation is total or needs an exchange rate entry to be created
    #     (self + writeoff_to_reconcile).check_full_reconcile()
    #     return True

    def _check_reconcile_validity(self):
        #Perform all checks on lines
        company_ids = set()
        all_accounts = []

        # print(self.id,' ddd')

        for line in self:
            company_ids.add(line.company_id.id)

            if line.partner_id == line.company_id.penjamin_id:
                if line.account_id == line.partner_id.account_repayment_id:
                    all_accounts.append(line.account_id)
            else:
                all_accounts.append(line.account_id)
            # print(line.account_id,' line.account_id')
            # print(line.account_id.name,' line.account_id.name')
            

            if (line.matched_debit_ids or line.matched_credit_ids) and line.reconciled:
                raise UserError(_('You are trying to reconcile some entries that are already reconciled.'))

        # print(len(set(all_accounts)),' nnnn')
        # print(len(set(all_accounts[0].reconcile)),' 2')
        # print(len(set(all_accounts[0].internal_type)),' 3')
        # exit()

        if len(company_ids) > 1:
            raise UserError(_('To reconcile the entries company should be the same for all entries.'))
        if len(set(all_accounts)) > 1:
            raise UserError(_('Entries are not from the same account.'))
            
        if len(set(all_accounts)) > 1 :
            if not (all_accounts[0].reconcile or all_accounts[0].internal_type == 'liquidity'):
                raise UserError(_('Account %s (%s) does not allow reconciliation. First change the configuration of this account to allow it.') % (all_accounts[0].name, all_accounts[0].code))


