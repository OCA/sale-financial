# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2011 Camptocamp SA (http://www.camptocamp.com)
#    All Right Reserved
#
#    Author : Yannick Vaucher (Camptocamp)
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

    def _convert_to_foreign_currency(self, cursor, user, pricelist, amount):
        pricelist_obj = self.pool.get('product.pricelist')
        currency_obj = self.pool.get('res.currency')
        user_obj = self.pool.get('res.users')
        pricelist = pricelist_obj.browse(cursor, user, pricelist)
        company_currency_id = user_obj.browse(cursor, user, user).company_id.currency_id.id
        price = currency_obj.compute(cursor, user,
                                     company_currency_id,
                                     pricelist.currency_id.id,
                                     amount,
                                     round=False)
        return price

    def _compute_purchase_price(self, cursor, user, ids, product_uom, pricelist, properties=None):
        '''
        Compute the purchase price

        As it explodes the sub product on 1 level

        This is not implemented for BoM having sub BoM producing more than 1
        product qty.
        Rewrite _compute_purchase_price and remove mrp constraint to fix this.
        '''
        if properties is None:
            properties =  []
        bom_obj = self.pool.get('mrp.bom')
        uom_obj = self.pool.get('product.uom')

        res = {}
        ids = ids or []

        for pr in self.browse(cursor, user, ids):

            # Workarount for first loading in V5 as some columns are not created
            if not hasattr(pr, 'standard_price'): return False
            bom_id = bom_obj._bom_find(cursor, user, pr.id, product_uom, properties)

            if bom_id:
                bom = bom_obj.browse(cursor, user, bom_id)

                sub_products, routes = bom_obj._bom_explode(cursor, user, bom, 1, properties, addthis=True)

                res[pr.id] = 0.0
                for spr in sub_products:
                    sub_product = self.browse(cursor, user, spr['product_id'])

                    if pricelist:
                        std_price = self._convert_to_foreign_currency(cursor, user,
                                                                      pricelist,
                                                                      sub_product.standard_price)
                    else:
                        std_price = sub_product.standard_price

                    qty = uom_obj._compute_qty(cursor, user,
                                               from_uom_id = spr['product_uom'],
                                               qty         = spr['product_qty'],
                                               to_uom_id   = sub_product.uom_po_id.id)

                    res[pr.id] += std_price * qty
                    # TODO use routes to compute cost of manufacturing
                    # sum routing hours * workcenter_cost_per_hour

            else:
                res[pr.id] = pr.standard_price

        return res


    def compute_markup(self, cursor, user, ids,
                       product_uom = None,
                       pricelist   = None,
                       sale_price  = None,
                       properties  = None,
                       context     = None):
        '''
        compute markup
        If properties, pricelist and sale_price arguments are set, it will be used to compute all results
        '''
        properties = properties or []
        pricelist = pricelist or []
        context = context or {}
        if isinstance(ids, (int, long)):
            ids =  [ids]
        res = {}

        # compute purchase prices, in order to take product with bom into account
        purchase_prices = self._compute_purchase_price(cursor, user, ids,
                                                       product_uom, pricelist, properties)

        # if purchase prices failed returned a dict of default values
        if not purchase_prices: return dict([(id, {'commercial_margin': 0.0,
                                                   'markup_rate': 0.0,
                                                   'cost_price': 0.0,}) for id in ids])


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
            res = _get_parent_bom(bom)
        final_bom_ids = list(set(res + bom_ids))
        return list(set(ids + self._get_product(cursor, user, final_bom_ids, context)))

    def _get_product(self, cursor, user, ids, context = None):
        context = context or {}

        bom_obj = self.pool.get('mrp.bom')

        res = {}
        for bom in bom_obj.browse(cursor, user, ids, context=context):
            res[bom.product_id.id] = True
        return res.keys()

    def _compute_all_markup(self, cursor, user, ids, field_name, arg, context = None):
        '''
        method for product function field on multi 'markup'
        '''
        res = self.compute_markup(cursor, user, ids, context=context)
        return res

    _store_cfg = {'product.product': (_get_bom_product, ['list_price' ,'standard_price'], 20),
                  'mrp.bom': (_get_product,
                             ['bom_id', 'bom_lines', 'product_id', 'product_uom',
                             'product_qty', 'product_uos', 'product_uos_qty',
                             'property_ids'], 20)}



    _columns = {'commercial_margin' : fields.function(_compute_all_markup,
                                                      method=True,
                                                      string='Margin',
                                                      digits_compute=dp.get_precision('Sale Price'),
                                                      store =_store_cfg,
                                                      multi ='markup',
                                                      help='Margin is [ sale_price - cost_price ]'),
                'markup_rate' : fields.function(_compute_all_markup,
                                            method=True,
                                            string='Markup rate (%)',
                                            digits_compute=dp.get_precision('Sale Price'),
                                            store=_store_cfg,
                                            multi='markup',
                                            help='Markup rate is [ margin / sale_price ]'),
                'cost_price' : fields.function(_compute_all_markup,
                                               method=True,
                                               string='Cost Price (incl. BOM)',
                                               digits_compute=dp.get_precision('Sale Price'),
                                               store=_store_cfg,
                                               multi='markup',
                                               help="The cost is the standard price unless the product is composed, "
                                                    "in that case it computes the price from its components")}
