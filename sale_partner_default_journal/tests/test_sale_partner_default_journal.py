# -*- coding: utf-8 -*-
# © 2016 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp.tests.common import TransactionCase


class TestSalePartnerDefaultJournal(TransactionCase):
    def test_sale_partner_default_journal(self):
        import pudb
        pudb.set_trace()
        # the installation should have found a journal

        p = self.env['res.partner'].create(
            { 'name': 'tstpartner','customer': True,
            })
        self.assertTrue(p.default_sale_journal_id)
        # check if changing this cascades to the children
        journal = self.env['account.journal'].create({
            'name': 'default sale journal',
            'code': 'def',
            'type': 'sale',
        })

        p.default_sale_journal_id = journal

        self.assertEqual(
            p.default_sale_journal_id,
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

        # create product deliverable and sale
        product_tmpl = self.env['product.template'].create({
            'name': 'Templatetest',
            'route_ids':[(6, 0,
                          [self.env.ref('purchase.route_warehouse0_buy').id,
                               self.env.ref('stock.route_warehouse0_mto').id])]
        })

        pricelist =  self.env['product.pricelist'].create({
            'active': True,
            'name': 'Test Pricelist',
            'currency_id': self.env.ref('base.EUR').id
        })

        product_sale = self.env['product.product'].create({
            'name': 'producttest',
            'product_tmpl_id': product_tmpl.id,
            'type': 'product'
        })

        sale = self.env['sale.order'].create({
            'partner_id': p.id,
            'partner_invoice_id': p.id,
            'partner_shipping_id': p.id,
            'order_line': [(0, 0, {'name': product_sale.name,
                                'product_id': product_sale.id,
                                'product_uom_qty': 2,
                                'product_uom': product_sale.uom_id.id,
                                'price_unit':  product_sale.list_price})],
            'pricelist_id': pricelist.id,
         })

        #create return journal and assign it

        journal_returns = self.env['account.journal'].create({
            'name': 'default return journal',
            'code': 'ret',
            'type': 'purchase',
        })
        p.default_return_journal_id = journal_returns

        #confirm the sale
        sale.force_quotation_send()
        sale.action_confirm()

        #make an invoice and verify it is on journal
        invoice_id =  sale.action_invoice_create()
        invoice = self.env['account.invoice'].browse(invoice_id)
        self.assertEqual(invoice.journal_id, p.default_sale_journal_id,
                         'default sale journal was not assigned to invoice'
                         'after sale confirmation')
        delivery = self.env['stock.picking'].search(
            ['|',
             ('group_id', '=', sale.procurement_group_id),
             ('origin', '=', sale.name)
            ] 
        )
        self.assertEqual(len(delivery), 1, 'sale generated more than one delivery' )

        # revert delivery
        return_wiz_model = self.env['stock.return.picking.line']
        return_wiz = return_wiz_model.create(
            {
                'product_id': product_sale.id,
                'quantity': 2
            })
        return_wiz.with_context(active_id=delivery.id)._create_returns()
        # validate
        delivery.do_new_transfer()

        # check sale has 2 deliveries
        sale.assertEqual(
            sale.delivery_count, 2,
            'The new delivery has not been created after a return'
        )

        sale.assertEqual(sale.invoice_count, 1, 'wrong number of invoices')
        # do invoice from sale

        invoice_id =  sale.action_invoice_create()





        # verify that we have 2 invoices , one with journal_default sale and
        # the other one with journal default returns and type out_refund











