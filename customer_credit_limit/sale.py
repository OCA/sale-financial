# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Sistemas Adhoc
#    Copyright (C) 2014 Eficent (<http://www.eficent.com/>)
#              <contact@eficent.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _


class sale_order(osv.osv):
    _inherit = "sale.order"

    def check_limit(self, cr, uid, ids, context=None):

        model_data_obj = self.pool.get('ir.model.data')
        res_groups_obj = self.pool.get('res.groups')

        for order_id in ids:
            processed_order = self.browse(cr, uid, order_id, context=context)
            if processed_order.order_policy == 'prepaid':
                continue
            partner = processed_order.partner_id
            credit = partner.credit

            # We sum from all the sale orders that are approved,
            # the sale order lines that are not yet invoiced
            order_obj = self.pool.get('sale.order')
            filters = [('partner_id', '=', partner.id),
                       ('state', '<>', 'draft'),
                       ('state', '<>', 'cancel')]
            approved_invoices_ids = order_obj.search(
                cr, uid, filters, context=context)
            approved_invoices_amount = 0.0
            for order in order_obj.browse(
                    cr, uid, approved_invoices_ids, context=context):
                for order_line in order.order_line:
                    if not order_line.invoiced:
                        approved_invoices_amount += order_line.price_subtotal

            # We sum from all the invoices that are in draft the total amount
            invoice_obj = self.pool.get('account.invoice')
            filters = [('partner_id', '=', partner.id),
                       ('state', '=', 'draft')]
            draft_invoices_ids = invoice_obj.search(
                cr, uid, filters, context=context)
            draft_invoices_amount = 0.0
            for invoice in invoice_obj.browse(
                    cr, uid, draft_invoices_ids, context=context):
                draft_invoices_amount += invoice.amount_total

            available_credit = partner.credit_limit \
                - credit \
                - approved_invoices_amount \
                - draft_invoices_amount

            group_releaser_id = model_data_obj._get_id(
                cr, uid, 'customer_credit_limit',
                'group_so_credit_block_releaser')
            if group_releaser_id:
                res_id = model_data_obj.read(cr, uid, [group_releaser_id],
                                             ['res_id'])[0]['res_id']
                group_releaser = res_groups_obj.browse(
                    cr, uid, res_id, context=context)
                group_user_ids = [user.id for user
                                  in group_releaser.users]

                if processed_order.amount_total > available_credit \
                        and uid not in group_user_ids:
                    raise osv.except_osv(
                        _('Credit exceeded'),
                        _('Cannot confirm the order since the '
                          'credit balance is %s You can still '
                          'process the Sales Order by changing '
                          'the Invoice Policy to "Before Delivery."')
                        % (available_credit,))

        return True
