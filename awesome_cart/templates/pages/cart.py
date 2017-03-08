# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals

no_cache = 1
no_sitemap = 1

import frappe
import json
from frappe import _

from erpnext.shopping_cart.cart import get_cart_quotation
from awesome_cart import cart
from awesome_cart.compat.frappe import login_context

from widgets_collection import login

def get_context(context):
    """This is a controller extension for erpnext.templates.pages.cart"""

    context["no_cache"] = 1

    settings = frappe.db.get("Awc Settings")

    # remove? shipping is essential here anyways
    context.shipping_enabled = 1 if settings.awc_shipping_enabled else 0

    # flag to display login form
    context.is_logged = cart.is_logged_in()
    login.apply_context(context)

    return context
