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
from awesome_cart.session import get_awc_session
from awesome_cart.power import has_role

from widgets_collection import login

no_cache = 1
no_sitemap = 1

def get_context(context):
	"""This is a controller extension for erpnext.templates.pages.cart"""

	context["no_cache"] = 1

	settings = frappe.db.get("Awc Settings")
	awc_session = get_awc_session()
	customer = get_current_customer()

	context["countries"] = [ x for x in frappe.get_list("Country", fields=["country_name", "name"], ignore_permissions=1) ]

	default_country = frappe.get_value("System Settings", "System Settings", "country")
	default_country_doc = next((x for x in context["countries"] if x.name == default_country), None)

	if frappe.session.user != "Guest":
		address_links = frappe.get_all("Dynamic Link", filters={"link_name" : customer.name}, fields=["parent"])
		addresses = []
		for address in address_links:
			addresses.extend(frappe.get_all("Address", filters={"name" : address.parent, "disabled" : False}, fields="*"))
		context['addresses'] = addresses

		customer_info = frappe.db.get_values("Customer", customer.name, ["has_shipping_account", "fedex_account_number"])[0]
		context["customer_info"] = {
			"has_shipping_acc": customer_info[0],
			"fedex_acc_number": customer_info[1]
		}

	country_idx = context["countries"].index(default_country_doc)
	context["countries"].pop(country_idx)
	context["countries"] = [default_country_doc] + context["countries"]

	context["shipping_rate_api"] = frappe.get_hooks("shipping_rate_api")[0]
	context["selected_customer"] = awc_session.get("selected_customer", False)

	# ensures clearing address and method selection when visiting checkout page as
	# shipping address widget won't pre-select them.
	awc.reset_shipping(None, awc_session=awc_session, customer=customer)

	# remove? shipping is essential here anyways
	context.shipping_enabled = 1 if settings.awc_shipping_enabled else 0

	related_items = []
	skus_in_cart = []
	# build upsell sku list using or building cache if necessary
	for item in awc_session.get("cart", {}).get("items", []):
		# build cart sku list to dedup later
		skus_in_cart += [item.get("sku")]

		# fetches related items to this sku
		item_related_items = awc.get_related_products_by_sku(
			item.get("sku"), awc_session=awc_session, customer=customer)

		# quick list deduping
		related_items = related_items + list(set(item_related_items) - set(related_items))

	# builds upsell item objects using cache if necessary
	upsell = []
	for sku in related_items:
		if sku not in skus_in_cart:
			# fetches product data to build upsell widget
			product_response = awc.get_product_by_sku(sku, awc_session=awc_session)
			if product_response.get("success"):
				upsell += [product_response.get("data")]

	# upsell widget data is made available to the context here
	context["upsell"] = dict(related_products=upsell)

	# flag to display login form
	context.is_logged = awc.is_logged_in()
	login.apply_context(context)

	if frappe.response.get("awc_alert"):
		context["awc_alert"] = frappe.response.get("awc_alert")

	user_doc = frappe.get_doc("User", frappe.session.user)

	context['enable_contacts'] = False

	if context["selected_customer"] and (user_doc.get("is_power_user") or \
		has_role([
			"Administrator",
			"Sales User",
			"Sales Manager",
			"System Manager"
		], user_doc.name)):

		# find olddest is_primary or oldest contact
		context['customer_contacts'] = frappe.db.sql("""
			SELECT
				c.name as name,
				c.email_id as email_id,
				c.first_name as first_name,
				c.last_name as last_name,
				c.is_primary_contact as is_primary_contact
			FROM
				`tabContact` c
			LEFT JOIN
				`tabDynamic Link` dl ON dl.parent=c.name
			WHERE
				dl.link_doctype='Customer' AND
				dl.link_name=%(customer_name)s
			ORDER BY 
				c.is_primary_contact DESC,
				c.creation asc
		""",
		{ "customer_name": context["selected_customer"]},
		as_dict=True)

		context['enable_contacts'] = True if len(context['customer_contacts']) > 1 else False

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
