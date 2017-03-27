# -*- coding: utf-8 -*-
# © 2016 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp import api, fields, models, _


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    @ api.multi
    def create_invoices(self):
        partner = self.env['sale.order'].browse(
            self.env.context.get('active_id')
	).partner_invoice_id
        result = super(
            SaleAdvancePaymentInv, self.with_context(
                default_sale_journal_id=partner.default_sale_journal_id.id
            )).create_invoices()   
        result.write({'journal_id': partner.default_sale_journal.id.id})
        return result

