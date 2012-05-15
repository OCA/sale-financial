# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Yannick Vaucher
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


class MrpBoM(Model):
    _inherit = 'mrp.bom'

    def _limit_produced_product_number(self, cursor, user, ids, context=None):
        """Add a constraint of to limit qty of product to 1 on BOM"""
        context = context or {}
        bom = self.browse(cursor, user, ids[0])
        if bom.product_qty != 1 and bom.bom_lines:
            return False
        return True



    _constraints = [(_limit_produced_product_number,
                     "sale_markup module doesn't allow you to have a"
                     "bom with product qty > 1.",
                     ['product_qty', 'bom_lines'])]
