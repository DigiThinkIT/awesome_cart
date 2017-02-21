from __future__ import unicode_literals


import json
import traceback
import frappe

from frappe import _
from frappe.utils import cint
from erpnext.shopping_cart import cart

from . import compat
from .compat import customer as compat_customer
from . import dbug

@frappe.whitelist(xss_safe=True)
def stored_payments(start=0, limit=5, action="query", payment_id=None):

	if action == "query":
		return fetch_stored_payments(start, limit)

	if action == "remove":
		return delete_stored_payment(payment_id)

def fetch_stored_payments(start, limit):

	result = {
		"success": True,
		"data": [],
		"total": 0
	}

	return result

def delete_stored_payment(payment_id):

	result = {
		"msg": "Not Implemented",
		"success": False
	}

	return result

@frappe.whitelist(xss_safe=True)
def addresses(start=0, limit=5, action="query", address_id=None):
	customer = compat_customer.get_current_customer()
	result = {
		"success": False,
		"msg": "Unknown Error"
	}

	if action == "query":
		if customer:
			try:
				addresses = compat_customer.fetch_addresses(
					customer_name=customer.name,
					start=start,
					limit=limit,
					order_by="is_primary_address DESC, is_shipping_address DESC, address_type DESC",
					ignore_permissions=True)

				total_addresses = compat_customer.total_addresses(customer)

				result["success"] = True
				result["data"] = addresses
				result["total"] = total_addresses
				result["msg"] = addresses
			except Exception as ex:
				result["success"] = False
				result["msg"] = str(ex)

		else:
			result["success"] = False
			result["msg"] = _("Customer Not Found.")

		return result

	if action == "remove":
		try:
			compat_customer.delete_address(customer.name, address_id)
		except compat_customer.AddressNotFoundError as anf:
			result["success"] = False
