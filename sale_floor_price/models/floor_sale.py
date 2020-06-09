# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2011 Camptocamp SA (http://www.camptocamp.com)
#    All Right Reserved
#
#    Author : Joel Grand-Guillaume (Camptocamp)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, models, _
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _reach_floor_price(self, floor_price, discount, price_unit):
        sell_price = price_unit * (1 - (discount or 0.0) / 100.0)
        precision =  self.env['decimal.precision'].precision_get('Sale Price')
        sell_price = round(sell_price, precision)
        if (sell_price < floor_price):
            return True
        return False

    def _compute_lowest_discount(self, floor_price, price_unit):
        diff = (floor_price - price_unit)
        disc = diff / price_unit
        return abs(round(disc*100, 2))

    def _compute_lowest_price(self, floor_price, discount):
        if discount == 100.0:
            res = 0.0
        else:
            res = floor_price / (1-(discount / 100.0))
        return res

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        '''
        Overload method:
            - Empty the discount when changing.
        '''
        res = super(SaleOrderLine, self).product_id_change()
        if 'discount' in res:
            res['discount'] = 0.0
        return res

    @api.multi
    @api.onchange('price_unit')
    def _onchange_price_unit(self):
        '''
        If price unit change, check that it is not < floor_price_limit of related product.
        If override_unit_price is True, we put in price_unit the min possible value, otherwise
        we leave it empty...
        '''       
        for line in self:
            result = self._check_floor_price(self, 
                line.price_unit, 
                line.product_id, 
                line.discount)
            if result:
                return result

    @api.onchange('product_id', 'price_unit', 'product_uom', 'product_uom_qty', 'tax_id')
    def _onchange_discount(self):
        '''
        If discount change, check that final price is not < floor_price_limit of related product
        '''
        res = super(SaleOrderLine, self)._onchange_discount()
        for line in self:
            result = self._check_floor_price(self, 
                line.price_unit, 
                line.product_id, 
                line.discount)
        return result

    def _check_floor_price(self, result, price_unit, product_id, discount):
        """
        result is a partially filled result dictionary, modified in place
        """
        res = {}
        if product_id and price_unit > 0.0:
            prod = result.product_id.floor_price_limit
            if self._reach_floor_price(prod, discount, price_unit):
                result.price_unit = self._compute_lowest_price(
                    prod, discount)
                substs = {'price_unit':price_unit,
                          'discount': discount,
                          'floor_price': prod,
                          'min_price': prod}
                warn_msg = _("You selected a unit price of %(price_unit)d.- with %(discount).2f discount.\n"
                             "The floor price has been set to %(floor_price)d.-,"
                             "so the mininum allowed value is %(min_price)d.") 

                warning = {'title': _('Floor price reached !'),
                           'message': warn_msg % substs}
                result['warning'] = warning
                result['domain'] = {}
