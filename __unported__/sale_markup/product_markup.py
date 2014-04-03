# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Yannick Vaucher, Joel Grand-Guillaume
#    Copyright 2011 Camptocamp SA
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

from openerp.osv import orm, fields
import decimal_precision as dp


class Product(orm.Model):
    _inherit = 'product.product'

    def _convert_to_foreign_currency(self, cr, uid, pricelist,
                                     amount_dict, context=None):
        """
        Apply purchase pricelist
        """
        if not pricelist:
            return amount_dict
        pricelist_obj = self.pool['product.pricelist']
        currency_obj = self.pool['res.currency']
        user_obj = self.pool['res.users']
        pricelist = pricelist_obj.browse(cr, uid, pricelist, context=context)
        user = user_obj.browse(cr, uid, uid, context=context)
        company_currency_id = user.company_id.currency_id.id
        converted_prices = {}
        for product_id, amount in amount_dict.iteritems():
            converted_prices[product_id] = currency_obj.compute(
                cr, uid, company_currency_id, pricelist.currency_id.id, amount,
                round=False)
        return converted_prices

    @staticmethod
    def _compute_markup(sale_price, purchase_price):
        """
        Return markup as a rate

        Markup = SP - PP / SP

        Where SP = Sale price
              PP = Purchase price
        """
        if not sale_price:
            return 0.0
        return sale_price - purchase_price / sale_price * 100

    def compute_markup(self, cr, uid, ids,
                       product_uom=None, pricelist=None, sale_price=None,
                       properties=None, context=None):
        """
        compute markup

        If properties, pricelist and sale_price arguments are set, it
        will be used to compute all results
        """
        properties = properties or []
        pricelist = pricelist or []
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = {}

        # cost_price_context will be used by product_get_cost_field if it is
        # installed
        cost_price_context = context.copy()
        cost_price_context.update({
            'product_uom': product_uom,
            'properties': properties})
        purchase_prices = self.get_cost_field(cr, uid, ids, cost_price_context)
        # if purchase prices failed returned a dict of default values
        if not purchase_prices:
            return dict([(id, {'commercial_margin': 0.0,
                               'markup_rate': 0.0,
                               'cost_price': 0.0,
                               }) for id in ids])

        purchase_prices = self._convert_to_foreign_currency(cr, uid, pricelist,
                                                            purchase_prices,
                                                            context=context)
        for pr in self.browse(cr, uid, ids, context=context):
            res[pr.id] = {}
            if sale_price is None:
                catalog_price = pr.list_price
            else:
                catalog_price = sale_price

            res[pr.id].update({
                'commercial_margin': catalog_price - purchase_prices[pr.id],
                'markup_rate': self._compute_markup(catalog_price,
                                                    purchase_prices[pr.id]),
                'cost_price': purchase_prices[pr.id]
            })

        return res

    def _get_bom_product(self, cr, uid, ids, context=None):
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
            result = []
            if bom_record.bom_id:
                result.append(bom_record.bom_id.id)
                result.extend(_get_parent_bom(bom_record.bom_id))
            return result
        res = []
        bom_obj = self.pool['mrp.bom']
        bom_ids = bom_obj.search(cr, uid, [('product_id', 'in', ids)],
                                 context=context)
        for bom in bom_obj.browse(cr, uid, bom_ids, context=context):
            res += _get_parent_bom(bom)
        final_bom_ids = list(set(res + bom_ids))
        return list(set(ids + self._get_product(cr, uid, final_bom_ids,
                                                context=context)))

    def _get_product(self, cr, uid, ids, context=None):
        bom_obj = self.pool['mrp.bom']

        res = {}
        for bom in bom_obj.browse(cr, uid, ids, context=context):
            res[bom.product_id.id] = True
        return res.keys()

    def _compute_all_markup(self, cr, uid, ids, field_name, arg,
                            context=None):
        """
        method for product function field on multi 'markup'
        """
        return self.compute_markup(cr, uid, ids, context=context)

    _store_cfg = {'product.product': (_get_bom_product,
                                      ['list_price', 'standard_price'], 20),
                  'mrp.bom': (_get_product,
                              ['bom_id', 'bom_lines', 'product_id',
                               'product_uom', 'product_qty', 'product_uos',
                               'product_uos_qty', 'property_ids'], 20)
                  }

    _columns = {
        'commercial_margin': fields.function(
            _compute_all_markup,
            string='Margin',
            digits_compute=dp.get_precision('Sale Price'),
            store=_store_cfg,
            multi='markup',
            help='Margin is [ sale_price - cost_price ] (not based on '
                 'historical values)'),
        'markup_rate': fields.function(
            _compute_all_markup,
            string='Markup',
            digits_compute=dp.get_precision('Sale Price'),
            store=_store_cfg,
            multi='markup',
            help='Markup is [ margin / sale_price ] (not based on '
                 'historical values)'),
    }
