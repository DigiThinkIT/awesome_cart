from __future__ import unicode_literals
import frappe

from awesome_cart.awc import get_awc_item_by_route

def get_context(context):

	path_parts = context.get("pathname", "").split('/')
	route = path_parts[1]
	if len(path_parts) > 2:
		cart_tag = path_parts[2]
	else:
		cart_tag = None

	awc_item, item = get_awc_item_by_route(route)

	if not item or not awc_item:
		frappe.local.flags.redirect_location = "404"
		raise frappe.Redirect

	for custom in awc_item.get('custom_data', []):
		if custom.key == 'redirect':
			frappe.local.flags.redirect_location = custom.value
			raise frappe.Redirect

	context["awc_item"] = awc_item
	context["item"] = item
	context["cart_tag"] = cart_tag
	context["title"] = item.get("item_name")

	return context
