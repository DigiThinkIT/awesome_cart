from __future__ import unicode_literals

import json
import traceback
import frappe

from frappe import _
from frappe.utils import cint
from erpnext.shopping_cart import cart

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
	if action == "query":
		return fetch_addresses(start, limit, "is_primary_address DESC, is_shipping_address DESC, address_type DESC")

	if action == "remove":
		return delete_address(address_id)

def delete_address(address_id):

	result = {
		"success": False,
		"msg": "",
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

def count_customer_addresses(customer):
	sql = "SELECT COUNT(*) FROM `tabDynamic Link` WHERE \
				parenttype='Address' \
				AND link_doctype='Customer' \
				AND link_name='{}'".format(customer)
	return cint(frappe.db.sql(sql, as_list=1)[0][0]);

def get_list_from_dynlinks(parent_dt, fields, link_dt, link_name, \
	order_by=None, limit=None, limit_start=None):
	if order_by:
		order_by = "ORDER BY {}".format(order_by)

	limit_start = 0 if not limit_start else cint(limit_start)
	limit = cint(limit) if limit else None



	# this is an a quick join to find all dt linked by a dynamic link
	sql = "SELECT {fields} FROM `tab{parent_dt}` a, \
			( \
				SELECT parent FROM `tabDynamic Link` \
					WHERE parenttype='{parent_dt}' \
					AND link_doctype='{link_dt}' \
					AND link_name='{link_name}' \
			) l \
			WHERE a.name = l.parent \
			{order_by} \
			{limit}".format(
				fields = ', '.join(['a.{}'.format(n) for n in fields]),
				parent_dt=parent_dt,
				link_dt=link_dt,
				link_name=link_name,
				order_by=order_by,
				limit="LIMIT {}, {}".format(limit_start, limit) if limit else ''
			)

	return frappe.db.sql(sql, as_dict=1)


def fetch_addresses(start, limit, order_by):
	result = {
		"success": False
	}

	try:
		session_user = frappe.get_user()
		user = frappe.get_doc("User", session_user.name)

		if user and user.email[-12:] == "@guest.local":
			return []

		quotation = cart.get_cart_quotation()["doc"]
		customer = frappe.get_doc("Customer", quotation.customer)

		total_addresses = count_customer_addresses(customer.name)

		addresses = get_list_from_dynlinks(
			"Address",
			fields=["address_title", "address_type", "address_line1",
				"address_line2", "city", "country", "state", "county", "pincode",
				"is_primary_address", "is_shipping_address", "name"],
			link_dt="Customer",
			link_name=customer.name,
			order_by=order_by,
			limit_start=start,
			limit=limit
		)

		#addresses = frappe.get_list("Address",
		#	fields=["address_title", "address_type", "address_line1",
		#		"address_line2", "city", "country", "state", "county", "pincode",
		#		"is_primary_address", "is_shipping_address", "name"],
		#	filters={ "customer": customer.name },
		#	order_by=order_by,
		#	limit_start=start,
		#	limit=limit,
		#	ignore_permissions=True)

		result['data'] = addresses
		result['total'] = total_addresses
		result['success'] = True
	except Exception as ex:
		result['exception'] = traceback.format_exc()
		result['success'] = False

	return result
