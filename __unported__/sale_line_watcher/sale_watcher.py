# -*- coding: utf-8 -*-
##############################################################################
#
#    Author:  Author Nicolas Bessi
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

from osv.orm import Model

class SaleOrderLine(Model):
    _inherit = 'sale.order.line'

    def onchange_price_unit(self, cr, uid, ids,
                            price_unit, product_id, discount, product_uom, pricelist,
                            **kwargs):
        '''
        Place holder function for onchange unit price
        '''
        res = {}
        return res

    def onchange_discount(self, cr, uid, ids,
                          price_unit, product_id, discount, product_uom, pricelist,
                          **kwargs):
        '''
        Place holder function for onchange discount
        '''
        res = {}
        return res

