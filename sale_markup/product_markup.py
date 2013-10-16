# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2011 Camptocamp SA (http://www.camptocamp.com)
#    All Right Reserved
#
#    Author : Yannick Vaucher, Joel Grand-Guillaume
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

from osv import fields
from osv.orm import Model
import decimal_precision as dp


class Product(Model):
    _inherit = 'product.product'

    def _convert_to_foreign_currency(self, cursor, user, pricelist, amount_dict, context=None):
        if context is None:
            context = {}
        if not pricelist:
            return amount_dict
        pricelist_obj = self.pool.get('product.pricelist')
        currency_obj = self.pool.get('res.currency')
        user_obj = self.pool.get('res.users')
        pricelist = pricelist_obj.browse(cursor, user, pricelist)
        company_currency_id = user_obj.browse(cursor, user, user).company_id.currency_id.id
        converted_price = {}
        for product_id, amount in amount_dict.iteritems():
            converted_price[product_id] = currency_obj.compute(cursor, user,
                                                               company_currency_id,
                                                               pricelist.currency_id.id,
                                                               amount,
                                                               round=False)
        return converted_price

    def compute_markup(self, cursor, user, ids,
                       product_uom = None,
                       pricelist   = None,
                       sale_price  = None,
                       properties  = None,
                       context     = None):
        '''
        compute markup

        If properties, pricelist and sale_price arguments are set, it
        will be used to compute all results
        '''
        properties = properties or []
        pricelist = pricelist or []
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids =  [ids]
        res = {}

        # cost_price_context will be used by product_get_cost_field if it is installed
        cost_price_context = context.copy().update({'produc_uom': product_uom,
                                                    'properties': properties})
        purchase_prices = self.get_cost_field(cursor, user, ids, cost_price_context)
        # if purchase prices failed returned a dict of default values
        if not purchase_prices: return dict([(id, {'commercial_margin': 0.0,
                                                   'markup_rate': 0.0,
                                                   'cost_price': 0.0,}) for id in ids])

        purchase_price = self._convert_to_foreign_currency(cursor, user, pricelist, purchase_prices)
        for pr in self.browse(cursor, user, ids):
            res[pr.id] = {}
            if sale_price is None:
                catalog_price = pr.list_price
            else:
                catalog_price = sale_price

            res[pr.id]['commercial_margin'] = catalog_price - purchase_prices[pr.id]

            res[pr.id]['markup_rate'] = (catalog_price and
                                         (catalog_price - purchase_prices[pr.id]) / catalog_price * 100 or 0.0)

            res[pr.id]['cost_price'] = purchase_prices[pr.id]

        return res

    def _get_bom_product(self,cursor, user, ids, context=None):
        """return ids of modified product and ids of all product that use
        as sub-product one of this ids. Ex:
        BoM :
            Product A
                -   Product B
                -   Product C
        => If we change standard_price of product B, we want to update Product
        A as well..."""
        if context is None:
            context = {}
        def _get_parent_bom(bom_record):
            """Recursvely find the parent bom"""
            result=[]
            if bom_record.bom_id:
                result.append(bom_record.bom_id.id)
                result.extend(_get_parent_bom(bom_record.bom_id))
            return result
        res = []
        bom_obj = self.pool.get('mrp.bom')
        bom_ids = bom_obj.search(cursor, user, [('product_id','in',ids)])
        for bom in bom_obj.browse(cursor, user, bom_ids):
            res += _get_parent_bom(bom)
        final_bom_ids = list(set(res + bom_ids))
        return list(set(ids + self._get_product(cursor, user, final_bom_ids, context)))

    def _get_product(self, cursor, user, ids, context = None):
        if context is None:
            context = {}
        bom_obj = self.pool.get('mrp.bom')

        res = {}
        for bom in bom_obj.browse(cursor, user, ids, context=context):
            res[bom.product_id.id] = True
        return res.keys()

    def _compute_all_markup(self, cursor, user, ids, field_name, arg, context = None):
        '''
        method for product function field on multi 'markup'
        '''
        if context is None:
            context = {}
        res = self.compute_markup(cursor, user, ids, context=context)
        return res

    _store_cfg = {'product.product': (_get_bom_product, ['list_price' ,'standard_price'], 20),
                  'mrp.bom': (_get_product,
                             ['bom_id', 'bom_lines', 'product_id', 'product_uom',
                             'product_qty', 'product_uos', 'product_uos_qty',
                             'property_ids'], 20)}



    _columns = {
        'commercial_margin' : fields.function(_compute_all_markup,
                                              method=True,
                                              string='Margin',
                                              digits_compute=dp.get_precision('Sale Price'),
                                              store =_store_cfg,
                                              multi ='markup',
                                              help='Margin is [ sale_price - cost_price ] (not based on historical values)'),
        'markup_rate' : fields.function(_compute_all_markup,
                                        method=True,
                                        string='Markup rate (%)',
                                        digits_compute=dp.get_precision('Sale Price'),
                                        store=_store_cfg,
                                        multi='markup',
                                        help='Markup rate is [ margin / sale_price ] (not based on historical values)'),
        }
