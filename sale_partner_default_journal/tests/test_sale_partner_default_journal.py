# -*- coding: utf-8 -*-
# © 2016 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp.tests.common import TransactionCase


class TestSalePartnerDefaultJournal(TransactionCase):
    def test_sale_partner_default_journal(self):
        # the installation should have found a journal
        p = self.env['res.partner'].create(
            {
                'name': 'partner1',
                'customer': True,
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

        # create product deliverable and sale
        product_tmpl = self.env['product.template'].create({
            'name': 'Templatetest',
            'route_ids':[(6, 0,
                          [self.env.ref('purchase.route_warehouse0_buy').id,
                           self.env.ref('stock.route_warehouse0_mto').id])],
            'invoice_policy': 'order'
        })

        pricelist =  self.env['product.pricelist'].create({
            'active': True,
            'name': 'Test Pricelist',
            'currency_id': self.env.ref('base.EUR').id
        })

        """
        VERY IMPORTANT:
            the creation of the return delivery invoice  will only be calculated 
            for products that have invoice_policy == delivery.
            If invoice policy is "order" the _get_to_invoice_qty will calculate
            the amount to invoice for the line as:
                line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced 
                this means that if it has already been invoiced in the outgoing
                delivery it will never be invoiced again. and the functions of the
                module "sale stock_picking_return_invoicing" are rendered mute.

            the 'delivery' policy insead calculates lines to invoice as

                line.qty_to_invoice = line.qty_delivered - line.qty_invoiced

            because qty_delivered compute field is overwritten in
            "sale_stock_picking_return_invoicing" this will manage correctly.

            https://github.com/OCA/account-invoicing/blob/9.0/sale_stock_picking_return_invoicing/models/sale_order.py#L12

            Example  our current client has this mix of products:

           invoice_policy | count 
           ----------------+-------
           delivery       |  5085
           order          |  3550


            possible solution:

                A) Make every product 'delivery'

                B) it is not possible to make everything "delivery", we should
                extend sale_stock_picking_return_invoicing to overwrite 
                def _get_to_invoice_qty(self) in sale order 
                and make it smarter. 
                """

        product_sale = self.env['product.product'].create({
            'name': 'producttest',
            'product_tmpl_id': product_tmpl.id,
            'list_sale': 12,
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
        sale.action_confirm()
        #sale.write({'state':'sale'})
        #make an invoice and verify it is on journal
        delivery = self.env['stock.picking'].search(
            ['|',
             ('group_id', '=', sale.procurement_group_id.id),
             ('origin', '=', sale.name)
            ] 
        )
        self.assertEqual(
            len(delivery), 1,
            'sale generated more than one delivery'
        )
        # invoice
        inv_confirm_wiz2 =  self.env['sale.advance.payment.inv'].create(
            {'advance_payment_method':  'delivered'}
        )
        inv_confirm_wiz2.with_context(active_ids=sale.id).create_invoices()
        self.assertEqual(sale.invoice_count, 1, 'wrong number of invoices')
        #pay invoice
        # revert delivery
        return_wiz_model = self.env['stock.return.picking']
        return_wiz = return_wiz_model.create(
            { 'location_id': self.env.ref('stock.stock_location_stock').id,
             'product_return_moves': [(
                 0, 0,
                 {   'to_refund_so':True,
                  'product_id': sale.order_line[0].product_id.id,
                  'quantity':  sale.order_line[0].product_uom_qty,
                  'move_id': sale.order_line[0].procurement_ids.move_ids.id
                 }
             )]
            }
        )
        delivery.do_new_transfer()
        # we have no stock force it.
        delivery.write({'state': 'done'})
        result_picking = return_wiz.with_context(
            active_id=delivery.id).create_returns()
        # confirm the new picking return
        return_delivery =  self.env['stock.picking'].browse(
            result_picking['res_id'])
        return_delivery.do_new_transfer()
        #force it
        return_delivery.write({'state': 'done'})
        # validate
        # check sale has 2 deliveries
        self.assertEqual(
            sale.delivery_count, 2,
            'The new delivery has not been created after a return'
        )









