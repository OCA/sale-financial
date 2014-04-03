# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Yannick Vaucher, Joel Grand-Guillaume
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
{'name' : 'Markup rate on product and sales',
 'version' : '5.1',
 'author' : 'Camptocamp',
 'maintainer': 'Camptocamp',
 'category': 'version',
 'complexity': "normal",
 'depends' : [
     'base',
     'product_get_cost_field',
     'mrp',
     'sale',
     'sale_floor_price'],
 'description': """
Markup rate on product and sales
================================

Display the product and sale markup in the appropriate views
""",
 'website': 'http://www.camptocamp.com/',
 'data': ['sale_view.xml',
          'product_view.xml'],
 'test': [],
 'installable': True,
 'auto_install': False,
 'license': 'AGPL-3',
 'application': True}


