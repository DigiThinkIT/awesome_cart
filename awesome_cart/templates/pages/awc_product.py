from __future__ import unicode_literals
import frappe

from awesome_cart.awc import get_awc_item_by_route

def get_context(context):

	path_parts = context.get("pathname", "").split('/')
	print(path_parts)
	route = path_parts[1]
	if len(path_parts) > 2:
		cart_tag = path_parts[2]
	else:
		cart_tag = None
	print(route)

	awc_item, item = get_awc_item_by_route(route)
	context["awc_item"] = awc_item
	context["item"] = item
	context["cart_tag"] = cart_tag
	context["title"] = item.get("name")

	if not item or not awc_item:
		frappe.local.flags.redirect_location = "404"
		raise frappe.Redirect

	return context
