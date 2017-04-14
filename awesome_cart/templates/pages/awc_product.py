from __future__ import unicode_literals
import frappe

from awesome_cart.awc import get_awc_item_by_route

def get_context(context):

    path_parts = context.get("pathname", "").split('/')
    route = path_parts[-1]
    print(route)

    awc_item, item = get_awc_item_by_route(route)
    context["awc_item"] = awc_item
    context["item"] = item
    if not item or not awc_item:
        frappe.local.flags.redirect_location = "404"
        raise frappe.Redirect

    return context
