# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals

no_cache = 1
no_sitemap = 1

import frappe
from erpnext.shopping_cart.cart import get_cart_quotation
from awesome_cart import cart
from awesome_cart.templates.pages import gateway
from awesome_cart.dbug import log

def get_context(context):
	"""This is a controller extension for erpnext.templates.pages.cart"""

	settings = frappe.db.get("Awc Settings")

	context.shipping_enabled = settings.awc_shipping_enabled

	#context.update(get_cart_quotation())
	context.is_logged = cart.is_logged()
	# update context with gateway setup
	gateway.get_context(context)
