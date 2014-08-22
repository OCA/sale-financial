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

from openerp.osv.orm import Model, fields
import decimal_precision as dp

def _prec(obj, cr, uid, mode=None):
    # This function use orm cache it should be efficient
    mode = mode or 'Sale Price'
    return obj.pool.get('decimal.precision').precision_get(cr, uid, mode)

class SaleOrder(Model):
    _inherit = 'sale.order'

    def _amount_all(self, cursor, user, ids, field_name, arg, context = None):
        '''Calculate the markup rate based on sums'''

        if context is None:
            context = {}
        res = {}
        res = super(SaleOrder, self)._amount_all(cursor, user, ids, field_name, arg, context)

        for sale_order in self.browse(cursor, user, ids):
            cost_sum = 0.0
            sale_sum = 0.0
            for line in sale_order.order_line:
                cost_sum += line.cost_price
                sale_sum += line.price_unit * (100 - line.discount) / 100.0
            res[sale_order.id]['markup_rate'] = sale_sum and (sale_sum - cost_sum) / sale_sum * 100 or 0.0
        return res


    def _get_order(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        result = set()
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result.add(line.order_id.id)
        return list(result)

    _store_sums = {
        'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
        'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty',
                'product_id','commercial_margin', 'markup_rate'], 10)}


    _columns = {'markup_rate': fields.function(_amount_all,
                                               method = True,
                                               string = 'Markup Rate',
                                               digits_compute=dp.get_precision('Sale Price'),
                                               store = _store_sums,
                                               multi='sums')}


class SaleOrderLine(Model):

    _inherit = 'sale.order.line'

    _columns = {'commercial_margin': fields.float('Margin',
                                                digits_compute=dp.get_precision('Sale Price'),
                                                help='Margin is [ sale_price - cost_price ],'
                                                     ' changing it will update the discount'),
                'markup_rate': fields.float('Markup Rate (%)',
                                            digits_compute=dp.get_precision('Sale Price'),
                                            help='Margin rate is [ margin / sale_price ],'
                                                 'changing it will update the discount'),
                'cost_price': fields.float('Historical Cost Price',
                                              digits_compute=dp.get_precision('Sale Price'),
                                              help="The cost price of the product at the time of the creation of the sale order"),
                 }
             


    def onchange_price_unit(self, cursor, uid, ids, price_unit, product_id, discount,
                            product_uom, pricelist, **kwargs):
        '''
        If price unit change, compute the new markup rate.
        '''
        res = super(SaleOrderLine,self).onchange_price_unit(cursor, uid, ids,
                                                            price_unit,
                                                            product_id,
                                                            discount,
                                                            product_uom,
                                                            pricelist)

        if product_id:
            product_obj = self.pool.get('product.product')
            if res['value'].has_key('price_unit'):
                price_unit = res['value']['price_unit']
            sale_price = price_unit * (100 - discount) / 100.0
            markup_res = product_obj.compute_markup(cursor, uid,
                                                    product_id,
                                                    product_uom,
                                                    pricelist,
                                                    sale_price)[product_id]


            res['value']['commercial_margin'] = round(markup_res['commercial_margin'], _prec(self, cursor, uid))
            res['value']['markup_rate'] = round(markup_res['markup_rate'],  _prec(self, cursor, uid))
        return res



    def onchange_discount(self, cursor, uid, ids,
                          price_unit, product_id, discount, product_uom, pricelist, **kwargs):
        '''
        If discount change, compute the new markup rate
        '''
        res = super(SaleOrderLine,self).onchange_discount(cursor, uid, ids,
                                                          price_unit,
                                                          product_id,
                                                          discount,
                                                          product_uom,
                                                          pricelist)
        
        if product_id:
            product_obj = self.pool.get('product.product')
            if res['value'].has_key('price_unit'):
                price_unit = res['value']['price_unit']
            if res['value'].has_key('discount'):
                discount = res['value']['discount']
            sale_price = price_unit * (100 - discount) / 100.0
            markup_res = product_obj.compute_markup(cursor, uid,
                                                    product_id,
                                                    product_uom,
                                                    pricelist,
                                                    sale_price)[product_id]


            res['value']['commercial_margin'] = round(markup_res['commercial_margin'] , _prec(self, cursor, uid))
            res['value']['markup_rate'] = round(markup_res['markup_rate'],  _prec(self, cursor, uid))
        return res


    def product_id_change(self, cursor, uid, ids, pricelist, product, qty=0,
                          uom=False, qty_uos=0, uos=False, name='', partner_id=False,
                          lang=False, update_tax=True, date_order=False, packaging=False,
                          fiscal_position=False, flag=False, discount=None, price_unit=None, context=None):
        '''
        Overload method
        If product change, compute the new markup.
        Added params : - price_unit,
                       - discount
                       - properties
        '''
        if context is None:
            context = {}
        discount = discount or 0.0
        price_unit = price_unit or 0.0
        res = {}
        res = super(SaleOrderLine, self).product_id_change(cursor, uid, ids, pricelist, product, qty,
                                                           uom, qty_uos, uos, name, partner_id,
                                                           lang, update_tax, date_order, packaging,
                                                           fiscal_position, flag, context)

        if product:
            if res['value'].has_key('price_unit'):
                price_unit = res['value']['price_unit']
            sale_price = price_unit * (100 - discount) / 100.0

            product_obj = self.pool.get('product.product')
            markup_res = product_obj.compute_markup(cursor, uid,
                                                    product,
                                                    uom,
                                                    pricelist,
                                                    sale_price)[product]

            res['value']['commercial_margin'] = round(markup_res['commercial_margin'],  _prec(self, cursor, uid))
            res['value']['markup_rate'] = round(int(markup_res['markup_rate'] * 100) / 100.0, _prec(self, cursor, uid))
            res['value']['cost_price'] = round(markup_res['cost_price'],  _prec(self, cursor, uid))

        return res


    def onchange_markup_rate(self, cursor, uid, ids,
                             markup, cost_price, price_unit, context=None):
        ''' If markup rate change compute the discount '''
        if context is None:
            context = {}
        res = {}
        res['value'] = {}
        markup = markup / 100.0
        if not price_unit or markup == 1: return {'value': {}}
        discount = 1 + cost_price / (markup - 1) / price_unit
        sale_price = price_unit * (1 - discount)
        res['value']['discount'] =  round(discount * 100,  _prec(self, cursor, uid))
        res['value']['commercial_margin'] = round(sale_price - cost_price, _prec(self, cursor, uid))
        return res


    def onchange_commercial_margin(self, cursor, uid, ids,
                                   margin, cost_price, price_unit, context=None):
        ''' If markup rate change compute the discount '''
        if context is None:
            context = {}
        res = {}
        res['value'] = {}
        if not price_unit: return {'value': {}}
        discount = 1 - ((cost_price + margin) / price_unit)
        sale_price = price_unit * (1 - discount)
        res['value']['discount'] = round(discount * 100,  _prec(self, cursor, uid))
        res['value']['markup_rate'] = round(margin / (sale_price or 1.0) * 100, _prec(self, cursor, uid))
        return res
