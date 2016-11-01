# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals

no_cache = 1
no_sitemap = 1

import frappe
from erpnext.shopping_cart.cart import get_cart_quotation

from awesome_cart import cart
from awesome_cart.templates.pages import gateway
from awesome_cart.dbug import log, json_default

def get_context(context):

	# get so_name from url (is there a better way?)
	pathname = context.get("pathname", "")
	parts = pathname.split('/')
	so_name = parts[-1]

	# fetch so doc
	so = frappe.get_doc("Sales Order", so_name)

	# fetch inv name
	inv_item = frappe.get_list("Sales Invoice Item", fields=["parent"], filters={"sales_order": so_name})[0]
	inv_name = inv_item.get('parent')

	settings = frappe.db.get("Awc Settings")
	context.no_cache = 1
	context.no_sitemap = 1
	context["inv_name"] = inv_name
	context["so_name"] = so_name
	context["user_email"] = so.contact_email

