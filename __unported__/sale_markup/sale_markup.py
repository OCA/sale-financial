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

from openerp.osv.orm import Model, fields
from openerp.addons import decimal_precision as dp
from openerp.tools import float_compare


def _prec(obj, cr, uid, mode=None):
    # This function use orm cache it should be efficient
    mode = mode or 'Sale Price'
    return obj.pool['decimal.precision'].precision_get(cr, uid, mode)


class SaleOrder(Model):
    _inherit = 'sale.order'

    def _amount_all(self, cr, user, ids, field_name, arg, context=None):
        """Calculate the markup rate based on sums"""

        res = super(SaleOrder, self
                    )._amount_all(cr, user, ids, field_name, arg,
                                  context=context)

        for sale_order in self.browse(cr, user, ids):
            cost_sum = 0.0
            sale_sum = 0.0
            for line in sale_order.order_line:
                cost_sum += line.cost_price
                sale_sum += line.price_unit * (100 - line.discount) / 100.0
            markup_rate = ((sale_sum - cost_sum) / sale_sum * 100 if sale_sum
                           else 0.0)
            res[sale_order.id]['markup_rate'] = markup_rate
        return res

    def _get_order(self, cr, uid, ids, context=None):
        sale_order_line_obj = self.pool['sale.order.line']
        sale_order_lines = sale_order_line_obj.browse(cr, uid, ids,
                                                      context=context)
        result = set()
        for line in sale_order_lines:
            result.add(line.order_id.id)
        return list(result)

    _store_sums = {
        'sale.order': (lambda self, cr, uid, ids, c={}: ids,
                       ['order_line'], 10),
        'sale.order.line': (_get_order,
                            ['price_unit', 'tax_id', 'discount',
                             'product_uom_qty', 'product_id',
                             'commercial_margin', 'markup_rate'], 10)
    }

    _columns = {
        'markup_rate': fields.function(
            _amount_all,
            string='Markup',
            digits_compute=dp.get_precision('Sale Price'),
            store=_store_sums,
            multi='sums'),
    }


class SaleOrderLine(Model):

    _inherit = 'sale.order.line'

    def _get_break(self, cr, uid, ids, field_name, arg, context=None):
        return dict.fromkeys(ids, False)

    _columns = {
        'commercial_margin': fields.float(
            'Margin',
            digits_compute=dp.get_precision('Sale Price'),
            help='Margin is [ sale_price - cost_price ], changing it will '
                 'update the discount'),
        'markup_rate': fields.float(
            'Markup',
            digits_compute=dp.get_precision('Sale Price'),
            help='Markup is [ margin / sale_price ], changing it will '
                 'update the discount'),
        'cost_price': fields.float(
            'Historical Cost Price',
            digits_compute=dp.get_precision('Sale Price'),
            help='The cost price of the product at the time of the creation '
                 'of the sale order'),
        # boolean fields to skip onchange loop
        'break_onchange_discount': fields.function(
            _get_break,
            string='Break onchange', type='boolean'),
        'break_onchange_markup_rate': fields.function(
            _get_break,
            string='Break onchange', type='boolean'),
        'break_onchange_commercial_margin': fields.function(
            _get_break,
            string='Break onchange', type='boolean'),
    }

    def onchange_price_unit(self, cr, uid, ids, context=None, **kwargs):
        """
        If price unit changes, compute the new markup rate and
        commercial margin

        context arguments:
            price_unit
            product_id
            discount
            product_uom
            pricelist
            markup_rate
            commercial_margin

        Will change:
            markup_rate
            commercial_margin
        """
        if context is None:
            context = {}
        res = super(SaleOrderLine, self
                    ).onchange_price_unit(cr, uid, ids, context=context)
        product_id = context.get('product_id')
        if product_id:
            price_unit = context.get('price_unit')
            discount = context.get('discount')
            product_uom = context.get('product_uom')
            pricelist = context.get('pricelist')
            product_obj = self.pool['product.product']
            markup = context.get('markup_rate', 0.0)
            margin = context.get('commercial_margin', 0.0)

            if 'price_unit' in res['value']:
                price_unit = res['value']['price_unit']
            sale_price = price_unit * (100 - discount) / 100.0
            markup_res = product_obj.compute_markup(cr, uid,
                                                    product_id,
                                                    product_uom,
                                                    pricelist,
                                                    sale_price)[product_id]

            new_margin = round(markup_res['commercial_margin'],
                               _prec(self, cr, uid))
            if not float_compare(margin, new_margin,
                                 precision_digits=_prec(self, cr, uid)) == 0:
                res['value'].update({
                    'commercial_margin': new_margin,
                    'break_onchange_commercial_margin': True,
                })
            new_markup = round(markup_res['markup_rate'],
                               _prec(self, cr, uid))
            if not float_compare(markup, new_markup,
                                 precision_digits=_prec(self, cr, uid)) == 0:
                res['value'].update({
                    'markup_rate': new_markup,
                    'break_onchange_markup_rate': True,
                })
        return res

    def onchange_discount(self, cr, uid, ids, context=None, **kwargs):
        """
        If discount changes, compute the new markup rate and commercial margin.

        context arguments:
            product_id
            price_unit
            discount
            product_uom
            pricelist
            markup_rate
            commercial_margin
            break_onchange

        Will change:
            markup_rate
            commercial_margin
        """
        if context is None:
            context = {}
        res = super(SaleOrderLine, self
                    ).onchange_discount(cr, uid, ids, context=context)
        product_id = context.get('product_id')
        if context.get('break_onchange'):
            res['value']['break_onchange_discount'] = False
        elif product_id:
            price_unit = context.get('price_unit')
            discount = context.get('discount')
            product_uom = context.get('product_uom')
            pricelist = context.get('pricelist')
            markup = context.get('markup_rate', 0.0)
            margin = context.get('commercial_margin', 0.0)

            product_obj = self.pool['product.product']
            if 'price_unit' in res['value']:
                price_unit = res['value']['price_unit']
            if 'discount' in res['value']:
                discount = res['value']['discount']
            sale_price = price_unit * (100 - discount) / 100.0
            markup_res = product_obj.compute_markup(cr, uid,
                                                    product_id,
                                                    product_uom,
                                                    pricelist,
                                                    sale_price)[product_id]

            new_margin = round(markup_res['commercial_margin'],
                               _prec(self, cr, uid))
            if not float_compare(margin, new_margin,
                                 precision_digits=_prec(self, cr, uid)) == 0:
                res['value'].update({
                    'commercial_margin': new_margin,
                    'break_onchange_commercial_margin': True,
                })
            new_markup = round(markup_res['markup_rate'],
                               _prec(self, cr, uid))
            if not float_compare(markup, new_markup,
                                 precision_digits=_prec(self, cr, uid)) == 0:
                res['value'].update({
                    'markup_rate': new_markup,
                    'break_onchange_markup_rate': True,
                })
        return res

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
                          uom=False, qty_uos=0, uos=False, name='',
                          partner_id=False, lang=False, update_tax=True,
                          date_order=False, packaging=False,
                          fiscal_position=False, flag=False,
                          context=None):
        """
        Overload method
        If product changes, compute the new markup, cost_price and
        commercial_margin.
        Added params : - price_unit
                       - discount
                       - markup_rate
                       - commercial_margin

        Will change:
            markup_rate
            commercial_margin
        """
        if context is None:
            context = {}
        res = super(SaleOrderLine, self
                    ).product_id_change(cr, uid, ids, pricelist, product, qty,
                                        uom, qty_uos, uos, name, partner_id,
                                        lang, update_tax, date_order,
                                        packaging, fiscal_position, flag,
                                        context=context)

        if product:
            price_unit = context.get('price_unit', 0.0)
            discount = context.get('discount', 0.0)
            markup = context.get('markup_rate', 0.0)
            margin = context.get('commercial_margin', 0.0)

            if 'price_unit' in res['value']:
                price_unit = res['value']['price_unit']
            sale_price = price_unit * (100 - discount) / 100.0

            product_obj = self.pool['product.product']
            markup_res = product_obj.compute_markup(cr, uid,
                                                    product,
                                                    uom,
                                                    pricelist,
                                                    sale_price)[product]

            res['value']['cost_price'] = round(markup_res['cost_price'],
                                               _prec(self, cr, uid))
            new_margin = round(markup_res['commercial_margin'],
                               _prec(self, cr, uid))
            if not float_compare(margin, new_margin,
                                 precision_digits=_prec(self, cr, uid)) == 0:
                res['value'].update({
                    'commercial_margin': new_margin,
                    'break_onchange_commercial_margin': True,
                })
            new_markup = round(int(markup_res['markup_rate'] * 100) / 100.0,
                               _prec(self, cr, uid))
            if not float_compare(markup, new_markup,
                                 precision_digits=_prec(self, cr, uid)) == 0:
                res['value'].update({
                    'markup_rate': new_markup,
                    'break_onchange_markup_rate': True,
                })

        return res

    def onchange_markup_rate(self, cr, uid, ids, context=None):
        """ If markup rate changes compute the discount

        context arguments:
            markup_rate
            commercial_margin
            cost_price
            price_unit
            break_onchange

        Will change:
            discount
            commercial_margin
        """
        if context is None:
            context = {}
        res = {'value': {}}
        if context.get('break_onchange'):
            res['value']['break_onchange_markup_rate'] = False
            return res

        markup = context.get('markup_rate')
        price_unit = context.get('price_unit')
        markup = markup / 100.0
        if price_unit and not markup == 1:
            cost_price = context.get('cost_price')
            margin = context.get('commercial_margin')
            discount = context.get('discount')

            new_discount = 1 + cost_price / (markup - 1) / price_unit
            sale_price = price_unit * (1 - new_discount)

            new_discount = round(new_discount * 100,  _prec(self, cr, uid))
            if not float_compare(discount, new_discount,
                                 precision_digits=_prec(self, cr, uid)) == 0:
                res['value'].update({
                    'discount': new_discount,
                    'break_onchange_discount': True,
                })

            new_margin = round(sale_price - cost_price, _prec(self, cr, uid))
            if not float_compare(margin, new_margin,
                                 precision_digits=_prec(self, cr, uid)) == 0:
                res['value'].update({
                    'commercial_margin': new_margin,
                    'break_onchange_commercial_margin': True,
                })
        return res

    def onchange_commercial_margin(self, cr, uid, ids, context=None):
        """ If commercial margin changes compute the discount

        context arguments:
            commercial_margin
            markup_rate
            discount
            cost_price
            price_unit
            break_onchange

        Will change:
            discount
            markup_rate
        """
        if context is None:
            context = {}
        res = {'value': {}}
        price_unit = context.get('price_unit')
        if context.get('break_onchange'):
            res['value']['break_onchange_commercial_margin'] = False
        elif price_unit:
            margin = context.get('commercial_margin')
            markup = context.get('markup_rate')
            cost_price = context.get('cost_price')
            discount = context.get('discount')

            new_discount = 1 - ((cost_price + margin) / price_unit)
            sale_price = price_unit * (1 - new_discount)

            new_discount = round(new_discount * 100,  _prec(self, cr, uid))
            if not float_compare(discount, new_discount,
                                 precision_digits=_prec(self, cr, uid)) == 0:
                res['value'].update({
                    'discount': new_discount,
                    'break_onchange_discount': True,
                })
            new_markup = round(margin / (sale_price or 1.0) * 100,
                               _prec(self, cr, uid))
            if not float_compare(markup, new_markup,
                                 precision_digits=_prec(self, cr, uid)) == 0:
                res['value'].update({
                    'markup_rate': new_markup,
                    'break_onchange_markup_rate': True,
                })
        return res
