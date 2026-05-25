# -*- coding: utf-8 -*-
# © 2016 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp.tests.common import TransactionCase


class TestSalePartnerDefaultJournal(TransactionCase):
    def test_sale_partner_default_journal(self):
        p = self.env.ref('base.res_partner_1')
        # the installation should have found a journal
        self.assertTrue(p.default_sale_journal_id)
        # check if changing this cascades to the children
        journal = self.env['account.journal'].create({
            'name': 'default sale journal',
            'code': 'def',
            'type': 'sale',
        })
        p.default_sale_journal_id = journal

        self.assertEqual(
            self.env.ref('base.res_partner_address_1').default_sale_journal_id,
            journal,
        )
        # invoice onchange
        invoice = self.env['account.invoice'].new({
            'type': 'out_invoice',
            'partner_id': p.id,
        })
        invoice._onchange_partner_id()
        self.assertEqual(journal.id, invoice.journal_id.id)
        # invoice created from order
        invoice_data = self.env['sale.order'].create({
            'partner_id': p.id,
        })._prepare_invoice()
        self.assertEqual(journal.id, invoice_data['journal_id'])
