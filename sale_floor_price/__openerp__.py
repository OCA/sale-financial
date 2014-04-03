# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Joël Grand-Guillaume
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
{'name' : 'Floor price on product',
 'version' : '5.1',
 'author' : 'Camptocamp',
 'maintainer': 'Camptocamp',
 'category': 'Sales Management',
 'complexity': "normal",
 'depends' : ['stock','product','sale', 'sale_line_watcher'],
 'description': """
Floor price on product
======================

Set a minimal price on product and raise a warning if sale price is too low
""",
 'website': 'http://www.camptocamp.com',
 'data': ['product_view.xml'],
 'test': [],
 'installable': True,
 'auto_install': False,
 'license': 'AGPL-3',
 'application': True}
