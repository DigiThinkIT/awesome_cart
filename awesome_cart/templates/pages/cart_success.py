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
	settings = frappe.db.get("Awc Settings")
	context["inv_name"] = frappe.session.get("awc_success_inv_name")
	context["so_name"] = frappe.session.get("awc_success_so_name")
	context["user_email"] = frappe.session.get("awc_success_email")

