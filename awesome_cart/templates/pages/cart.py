# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals

no_cache = 1
no_sitemap = 1

import frappe
from erpnext.shopping_cart.cart import get_cart_quotation
from awesome_cart import cart
from dti_gateway_manager.templates.pages import gateway

def get_context(context):
	context.update(get_cart_quotation())
	context.is_logged = cart.is_logged()

	# update context with gateway setup
	gateway.get_context(context)
