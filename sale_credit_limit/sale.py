# -*- encoding: utf-8 -*-
##############################################################################
#
#    Sale Credit Limit module for Odoo/OpenERP
#    Copyright (C) 2013-2014 Akretion (http://www.akretion.com)
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
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

from openerp.osv import orm
from openerp.tools.translate import _
import logging

logger = logging.getLogger('sale_credit_limit')


class res_partner(orm.Model):
    _inherit = "res.partner"

    # I think this should be part of the core
    # but I don't want to spend time arguing about it
    # and wait 6 months to have a merge proposal accepted
    def _commercial_fields(self, cr, uid, context=None):
        res = super(res_partner, self)._commercial_fields(
            cr, uid, context=context)
        if 'credit_limit' not in res:
            res.append('credit_limit')
        return res


class sale_order(orm.Model):
    _inherit = 'sale.order'

    def check_credit_limit(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids, context=context):
            if order.currency_id.id != order.company_id.currency_id.id:
                total_so_company_currency = self.pool['res.currency'].compute(
                    cr, uid, order.currency_id.id,
                    order.company_id.currency_id.id, order.amount_total,
                    context=context)
            else:
                total_so_company_currency = order.amount_total
            partner_balance = (
                order.partner_id.parent_id
                and order.partner_id.parent_id.credit
                or order.partner_id.credit)
            partner_credit_limit = order.partner_id.credit_limit
            partner_name = (
                order.partner_id.parent_id
                and order.partner_id.parent_id.name
                or order.partner_id.name)
            # should we take into account the confirmed sale order that are
            # not invoiced yet ?
            if (
                    partner_balance + total_so_company_currency
                    > partner_credit_limit):
                company_cur_symbol = order.company_id.currency_id.symbol
                raise orm.except_orm(
                    _('Credit Limit Check:'),
                    _("The balance of customer '%s' is %s %s.\nThis sale "
                        "order %s has a total amount of %s %s.\nThe sum of "
                        "these two amounts (%s %s) is over the credit limit "
                        "of %s %s for this customer.\n\nYou should wait for "
                        "this customer to make new payments or raise his "
                        "credit limit.") % (
                        partner_name, partner_balance, company_cur_symbol,
                        order.name, total_so_company_currency,
                        company_cur_symbol,
                        total_so_company_currency + partner_balance,
                        company_cur_symbol, partner_credit_limit,
                        company_cur_symbol))
            else:
                company_cur = order.company_id.currency_id.name
                logger.info(
                    'The balance of partner %s is %s %s'
                    % (partner_name, partner_balance, company_cur))
                logger.info(
                    'The sale order %s has a total amount of %s %s'
                    % (order.name, total_so_company_currency, company_cur))
                logger.info(
                    'Credit limit for partner %s is %s %s'
                    % (partner_name, partner_credit_limit, company_cur))
                logger.info(
                    'Therefore the sale order %s is accepted' % order.name)

        return True

    def action_button_confirm(self, cr, uid, ids, context=None):
        self.check_credit_limit(cr, uid, ids, context=context)
        return super(sale_order, self).action_button_confirm(
            cr, uid, ids, context=context)
