# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals

import frappe
import json
from frappe import _

from erpnext.shopping_cart.cart import get_cart_quotation
from awesome_cart import awc
from awesome_cart.compat.frappe import login_context
from awesome_cart.compat.customer import get_current_customer

from widgets_collection import login

no_cache = 1
no_sitemap = 1

def get_context(context):
	"""This is a controller extension for erpnext.templates.pages.cart"""

	context["no_cache"] = 1

	settings = frappe.db.get("Awc Settings")

	context["countries"] = [ x for x in frappe.get_list("Country", fields=["country_name", "name"], ignore_permissions=1) ]

	default_country = frappe.get_value("System Settings", "System Settings", "country")
	default_country_doc = next((x for x in context["countries"] if x.name == default_country), None)

	if frappe.session.user != "Guest":
		context["addresses"] = frappe.get_all("Address", filters={"customer" : get_current_customer().name, "disabled": False}, fields="*")
	
	country_idx = context["countries"].index(default_country_doc)
	context["countries"].pop(country_idx)
	context["countries"] = [default_country_doc] + context["countries"]

	context["shipping_rate_api"] = frappe.get_hooks("shipping_rate_api")[0]

	# remove? shipping is essential here anyways
	context.shipping_enabled = 1 if settings.awc_shipping_enabled else 0

	# flag to display login form
	context.is_logged = awc.is_logged_in()
	login.apply_context(context)

	if context.is_logged:
		# load gateway provider into context
		gateway_provider = frappe.get_hooks('awc_gateway_form_provider')
		if gateway_provider and len(gateway_provider) > 0:
			context['gateway_provider'] = frappe.call(gateway_provider[0], context=dict(
				use_address_same_as=1,
				address_same_as_label="Same as Shipping Address",
				address_same_as_source="#awc-shipping-form"
			))

	return context
