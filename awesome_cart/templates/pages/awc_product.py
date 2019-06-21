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
	print("----------------------------------")
	print(route)
	print(awc_item)
	print(item)
	print(path_parts)

	if awc_item:
		for custom in awc_item.get('custom_data', []):
			if custom.key == 'redirect':
				frappe.local.flags.redirect_location = custom.value
				raise frappe.Redirect

	if not item or not awc_item or not item.show_in_website:
		print("No item found?")
		frappe.local.flags.redirect_location = "404"
		raise frappe.Redirect

	context["awc_item"] = awc_item
	context["item"] = item
	context["cart_tag"] = cart_tag
	context["title"] = item.get("item_name")

	return context
