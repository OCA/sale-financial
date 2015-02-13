# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Joël Grand-Guillaume
#    Copyright 2012 Camptocamp SA
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

from openerp.osv.orm import Model
from openerp.tools.translate import _


class SaleOrderLine(Model):
    _inherit = 'sale.order.line'

    def _reach_floor_price(self, cr, uid, floor_price, discount, price_unit):
        sell_price = price_unit * (1 - (discount or 0.0) / 100.0)
        precision_obj = self.pool['decimal.precision']
        precision = precision_obj.precision_get(cr, uid, 'Sale Price')
        sell_price = round(sell_price, precision)
        if (sell_price < floor_price):
            return True
        return False

    def _compute_lowest_discount(self, cr, uid, floor_price, price_unit):
        diff = (floor_price - price_unit)
        disc = diff / price_unit
        return abs(round(disc * 100, 2))

    def _compute_lowest_price(self, cr, uid, floor_price, discount):
        if discount == 100.0:
            res = 0.0
        else:
            res = floor_price / (1 - (discount / 100.0))
        return res

    def product_id_change(self, cr, uid, ids, *args, **kwargs):
        """
        Overload method:
            - Empty the discount when changing.
        """
        res = super(SaleOrderLine, self
                    ).product_id_change(cr, uid, ids, *args, **kwargs)
        res['value']['discount'] = 0.0
        return res

    def onchange_price_unit(self, cr, uid, ids, context=None, **kwargs):
        """
        If price unit change, check that it is not < floor_price_limit of
        related product.
        If override_unit_price is True, we put in price_unit the min possible
        value, otherwise we leave it empty...
        """
        override_unit_price = kwargs.pop('override_unit_price', True)
        res = super(SaleOrderLine, self).onchange_price_unit(
            cr, uid, ids, context=context, **kwargs
        )
        price_unit = context.get('price_unit')
        product_id = context.get('product_id')
        discount = context.get('discount')
        self._check_floor_price(cr, uid, res, price_unit, product_id, discount,
                                override_unit_price)
        return res

    def onchange_discount(self, cr, uid, ids, context=None, **kwargs):
        """
        If discount change, check that final price is not < floor_price_limit
        of related product

        context price_unit, product_id, discount
        """
        if context is None:
            context = {}
        res = super(SaleOrderLine, self).onchange_discount(
            cr, uid, ids, context=context, **kwargs
        )
        price_unit = context.get('price_unit')
        product_id = context.get('product_id')
        discount = context.get('discount')

        self._check_floor_price(cr, uid, res, price_unit, product_id, discount)
        return res

    def _check_floor_price(self, cr, uid, result, price_unit, product_id,
                           discount, override_unit_price=True):
        """
        result is a partially filled result dictionary, modified in place
        """
        if 'value' not in result:
            result['value'] = {}
        if product_id and price_unit > 0.0:
            product_obj = self.pool['product.product']
            prod = product_obj.browse(cr, uid, product_id)
            if self._reach_floor_price(cr, uid, prod.floor_price_limit,
                                       discount, price_unit):
                if override_unit_price:
                    result['value']['price_unit'] = self._compute_lowest_price(
                        cr, uid, prod.floor_price_limit, discount)
                else:
                    result['value']['price_unit'] = price_unit
                substs = {'price_unit': price_unit,
                          'discount': discount,
                          'floor_price': prod.floor_price_limit,
                          'min_price': result['value']['price_unit']}
                warn_msg = _("You selected a unit price of %(price_unit)d.-"
                             "with %(discount).2f discount.\n"
                             "The floor price has been set to "
                             "%(floor_price)d.-, so the mininum allowed value "
                             "is %(min_price)d.")

                warning = {'title': _('Floor price reached !'),
                           'message': warn_msg % substs}
                result['warning'] = warning
                result['domain'] = {}
