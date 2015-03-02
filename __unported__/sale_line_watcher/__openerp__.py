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
{'name' : 'Sale order line watcher',
 'version' : '0.1',
 'author' : "Camptocamp,Odoo Community Association (OCA)",
 'maintainer': 'Camptocamp',
 'category': 'Hidden',
 'complexity': "normal",  # easy, normal, expert
 'depends' : ['base', 'sale'],
 'description': """Add new base onchange methods on sale_order class

 onchange_price_unit and onchange_discount both accept the following arguments:
 (self, cr, uid, ids, price_unit, product_id, discount, product_uom, pricelist, **kwargs)
""",
 'website': 'http://www.camptocamp.com',
 'init_xml': [],
 'update_xml': ['sale_view.xml'],
 'demo_xml': [],
 'tests': [],
 'installable': False,
 'auto_install': False,
 'license': 'AGPL-3',
 'application': True}
