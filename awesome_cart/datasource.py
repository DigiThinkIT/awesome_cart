from __future__ import unicode_literals

import json
import frappe

from frappe import _
from erpnext.shopping_cart import cart

from . import dbug

@frappe.whitelist(xss_safe=True)
def billing_addresses(start=0, limit=5, action="query", address_id=None):
	if action == "query":
		return fetch_addresses(start, limit, "Billing", "is_primary_address DESC")
	
	if action == "remove":
		return delete_address(address_id)

@frappe.whitelist(xss_safe=True)
def shipping_addresses(start=0, limit=5, action="query", address_id=None):

	if action == "query":
		return fetch_addresses(start, limit, "Shipping", "is_shipping_address DESC")

	if action == "remove":
		return delete_address(address_id)

def delete_address(address_id):

	result = {
		"success": False,
		"msg": ""
	}

	if not address_id:
		result['success'] = False
		result['msg'] = 'Missing address_id'
		return result

	session_user = frappe.get_user()
	user = frappe.get_doc("User", session_user.name)
	
	if user and user.email[-12:] == "@guest.local":
		return []
	
	quotation = cart.get_cart_quotation()["doc"]
	customer = frappe.get_doc("Customer", quotation.customer)

	address = frappe.get_doc("Address", address_id)

	# sanity check to make sure we only delete addresses which belong
	# to the customer in session
	if address and address.customer == customer.name:
		frappe.delete_doc("Address", address_id, ignore_permissions=True)
		result["success"] = True
	else:
		result["msg"] = "Address Not Found"

	return result

def fetch_addresses(start, limit, address_type, order_by):

	session_user = frappe.get_user()
	user = frappe.get_doc("User", session_user.name)
	
	if user and user.email[-12:] == "@guest.local":
		return []

	quotation = cart.get_cart_quotation()["doc"]
	customer = frappe.get_doc("Customer", quotation.customer)

	addresses = frappe.get_list("Address", 
		fields=["address_title", "address_type", "address_line1", "address_line2", "city", "country", "state", "county", "pincode", "is_primary_address", "is_shipping_address", "name"], 
		filters={"customer": customer.name, "address_type": address_type},
		order_by=order_by,
		limit_start=start,
		limit=limit)

	return addresses
