# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Yannick Vaucher
#    Copyright 2014 Camptocamp SA
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
import openerp.tests.common as common
from openerp.addons import get_module_resource


def _trigger_on_changes(self, cr, uid, sale_order, view_values, changed_values):
    triggered_on_changes = []
    while [i for i in changed_values.keys() if i not in triggered_on_changes]:
        res_values = {}
        for field in view_values.keys():
            if field in triggered_on_changes:
                continue
            triggered_on_changes.append(field)
            if field == 'product_id':
                res_values = self.SaleOrderLine.product_id_change(
                    cr, uid, False,
                    sale_order.pricelist_id.id,
                    view_values.get('product_id'),
                    qty=view_values.get('product_uom_qty'),
                    uom=False,
                    qty_uos=view_values.get('product_uos_qty'),
                    uos=False,
                    name='sol_test_1',
                    partner_id=sale_order.partner_id.id,
                    lang=False,
                    update_tax=True,
                    date_order=sale_order.date_order,
                    packaging=False,
                    fiscal_position=sale_order.fiscal_position.id,
                    flag=False,
                    context=view_values)
                break
            elif field == 'price_unit':
                res_values = self.SaleOrderLine.onchange_price_unit(cr, uid, False, context=view_values)
                break
            elif field == 'discount':
                res_values = self.SaleOrderLine.onchange_discount(cr, uid, False, context=view_values)
                break
            elif field == 'commercial_margin':
                res_values = self.SaleOrderLine.onchange_commercial_margin(cr, uid, False, context=view_values)
                break
            elif field == 'markup_rate':
                res_values = self.SaleOrderLine.onchange_markup_rate(cr, uid, False, context=view_values)
                break
        if res_values:
            changed_values.update(res_values['value'])
            view_values.update(res_values['value'])
    return view_values

class test_sale_markup(common.TransactionCase):
    """ Test the wizard for delivery carrier label generation """

    def setUp(self):
        super(test_sale_markup, self).setUp()
        cr, uid = self.cr, self.uid

        self.SaleOrder = self.registry('sale.order')
        self.SaleOrderLine = self.registry('sale.order.line')
        self.Product = self.registry('product.product')
        self.product_33 = self.Product.browse(
                cr, uid, self.ref('product.product_product_33'))
        self.ResPartner = self.registry('res.partner')
        self.partner_12 = self.ResPartner.browse(
                cr, uid, self.ref('base.res_partner_12'))

    def test_00_create_sale_order(self):
        """ Check markup computing in sale order

        And check each on_changes
        """
        cr, uid = self.cr, self.uid

        so_data = {'partner_id': self.partner_12.id,
                }
        res = self.SaleOrder.onchange_partner_id(cr, uid, False, self.partner_12.id)
        so_data.update(res['value'])

        so_1_id = self.SaleOrder.create(cr, uid, so_data)
        so_1 = self.SaleOrder.browse(cr, uid, so_1_id)

        ctx = {'product_id': self.product_33.id,
               'product_uom': self.ref('product.product_uom_unit'),
               'discount': 0.0,
               'product_uom_qty': 1,
               'product_uos_qty': 1,
               'sequence': 10,
               'state': 'draft',
               'type': 'make_to_stock',
               'price_unit': 0.0,
               'order_id': so_1_id,
               }

        # I set product A on sale order and trigger the on_change on product.
        res = self.SaleOrderLine.product_id_change(
            cr, uid, False,
            so_1.pricelist_id.id,
            ctx.get('product_id'),
            qty=ctx.get('product_uom_qty'),
            uom=False,
            qty_uos=ctx.get('product_uos_qty'),
            uos=False,
            name='sol_test_1',
            partner_id=so_1.partner_id.id,
            lang=False,
            update_tax=True,
            date_order=so_1.date_order,
            packaging=False,
            fiscal_position=so_1.fiscal_position.id,
            flag=False,
            context=ctx)

        ctx.update(res['value'])
        res = _trigger_on_changes(self, cr, uid, so_1, ctx, res['value'])
        # cost_price should be set and equal to product cost price.
        assert abs(res.get('cost_price') - self.Product.get_cost_field(cr, uid, self.product_33.id)[self.product_33.id]) < 0.01

        # commercial_margin should be updated and equal to price_unit * (1 - (discount / 100.0)) - cost_price
        commercial_margin = (ctx.get('price_unit') * (1 - (ctx.get('discount') / 100.0)) - ctx.get('cost_price'))
        assert abs(ctx.get('commercial_margin') - commercial_margin) < 0.01, "Commercial margin is %s instead of %s after update of product_id" % (ctx.get('commercial_margin'), commercial_margin)
        # markup_rate should be updated and equal to commercial_margin / (price_unit * (1 - (discount / 100.0)))
        markup_rate = (ctx.get('commercial_margin') / (ctx.get('price_unit') * (1 - (ctx.get('discount') / 100.0))) * 100.0)
        assert abs(ctx.get('markup_rate') - markup_rate) < 0.01, "Markup rate is %s instead of %s after update of product_id" % (ctx.get('markup_rate'), markup_rate)

        # I add 1 percent to discount and trigger the on_change on discount.
        ctx['discount'] = 1.0
        res = self.SaleOrderLine.onchange_discount(cr, uid, False, context=ctx)
        ctx.update(res['value'])
        ctx = _trigger_on_changes(self, cr, uid, so_1, ctx, res['value'])

        # commercial_margin should be updated and equal to price_unit * (1 - (discount / 100.0)) - cost_price
        commercial_margin = (ctx.get('price_unit') * (1 - (ctx.get('discount') / 100.0)) - ctx.get('cost_price'))
        assert abs(ctx.get('commercial_margin') - commercial_margin) < 0.01, "Commercial margin is %s instead of %s after update of discount" % (ctx.get('commercial_margin'), commercial_margin)

        # markup_rate should be updated and equal to commercial_margin / (price_unit * (1 - (discount / 100.0)))
        markup_rate = (ctx.get('commercial_margin') / (ctx.get('price_unit') * (1 - (ctx.get('discount') / 100.0))) * 100.0)
        assert abs(ctx.get('markup_rate') - markup_rate) < 0.01, "Markup rate is %s instead of %s after update of discount" % (ctx.get('markup_rate'), markup_rate)

        # I change the markup rate to 20.0 and trigger the on_change on markup_rate.
        ctx['markup_rate'] = 20.0
        res = self.SaleOrderLine.onchange_markup_rate(cr, uid, False, context=ctx)
        ctx.update(res['value'])
        ctx = _trigger_on_changes(self, cr, uid, so_1, ctx, res['value'])

        # commercial_margin should be updated and equal to price_unit * (1 - (discount / 100.0)) - cost_price
        commercial_margin = (ctx.get('price_unit') * (1 - (ctx.get('discount') / 100.0)) - ctx.get('cost_price'))
        assert abs(ctx.get('commercial_margin') - commercial_margin) < 0.01, "Commercial margin is %s instead of %s after update of markup_rate" % (ctx.get('commercial_margin'), commercial_margin)

        # markup_rate should be updated and equal to commercial_margin / (price_unit * (1 - (discount / 100.0)))
        markup_rate = (ctx.get('commercial_margin') / (ctx.get('price_unit') * (1 - (ctx.get('discount') / 100.0))) * 100.0)
        assert abs(ctx.get('markup_rate') - markup_rate) < 0.01, "Markup rate is %s instead of %s after update of markup_rate" % (ctx.get('markup_rate'), markup_rate)


        # I change the price unit to 2000.0 and trigger the on_change on price_unit.
        ctx['price_unit'] = 2000.0
        res = self.SaleOrderLine.onchange_price_unit(cr, uid, False, context=ctx)
        ctx.update(res['value'])
        ctx = _trigger_on_changes(self, cr, uid, so_1, ctx, res['value'])

        # commercial_margin should be updated and equal to price_unit * (1 - (discount / 100.0)) - cost_price
        commercial_margin = (ctx.get('price_unit') * (1 - (ctx.get('discount') / 100.0)) - ctx.get('cost_price'))
        assert abs(ctx.get('commercial_margin') - commercial_margin) < 0.01, "Commercial margin is %s instead of %s after update of price_unit" % (ctx.get('commercial_margin'), commercial_margin)

        # markup_rate should be updated and equal to commercial_margin / (price_unit * (1 - (discount / 100.0)))
        markup_rate = (ctx.get('commercial_margin') / (ctx.get('price_unit') * (1 - (ctx.get('discount') / 100.0))) * 100.0)
        assert abs(ctx.get('markup_rate') - markup_rate) < 0.01, "Markup rate is %s instead of %s after update of price_unit" % (ctx.get('markup_rate'), markup_rate)

        sol_data = ctx

        # I create the sale order line for the sale order.
        sol_1_id = self.SaleOrderLine.create(
            cr, uid,
            sol_data
            )

        so_1.refresh()
        assert so_1.markup_rate
        # as we have only one line it should be equal to our last line markup
        assert abs(so_1.markup_rate - markup_rate) < 0.01
