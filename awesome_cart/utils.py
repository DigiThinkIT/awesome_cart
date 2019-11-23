# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import os

import frappe
import traceback

from frappe import _
from frappe.utils import random_string

from .session import clear_awc_session, clear_cache_keys
from .compat.customer import get_current_customer
from .awesome_cart.doctype.awc_coupon.awc_coupon import is_coupon_valid as _is_coupon_valid

from dti_devtools.debug import log, pretty_json

def update_context(context):

	path = frappe.local.request.path[1:]
	context.current_date = ''


def on_session_creation(login_manager):
	pass


def on_logout(login_manager):

	clear_awc_session()

	# destroys cart session on logout
	sid = frappe.local.session.get(
		"awc_sid", frappe.local.request.cookies.get("awc_sid"))
	if sid:
		awc_sid = "awc_session_{0}".format(sid)
		frappe.cache().set_value(awc_sid, None)

@frappe.whitelist()
def get_order_data():
	sales_orders = frappe.get_all("Sales Order", filters={
		"owner": frappe.session.user}, limit_page_length=1, order_by="creation DESC")
	if sales_orders:
		order_doc = frappe.get_doc("Sales Order", sales_orders[0].get("name"))

		items_data = []
		for item in order_doc.items:
			items_data.append(
				[{
					'sku': item.item_code,
					'name': item.item_name,
					'price': item.rate,
					'quantity': item.qty
				}])

		transaction_data = {
			'transactionId': order_doc.name,
			'transactionTotal': order_doc.grand_total,
			'transactionShipping': order_doc.total_taxes_and_charges,
			'transactionProducts': items_data
		}

		return transaction_data

@frappe.whitelist()
def delete_address(address_name):
	frappe.db.set_value("Address", address_name, "disabled", 1)

@frappe.whitelist()
def edit_address(address):
	address =  json.loads(address)
	add_doc = frappe.get_doc("Address", address.get('address_name'))
	update_address(add_doc, address)

@frappe.whitelist()
def new_address(address):
	address =  json.loads(address)
	add_doc = frappe.new_doc("Address")
	update_address(add_doc, address)

	frappe.response.address_name = add_doc.name

	return add_doc.as_dict()

def update_address(add_doc, address):
	add_doc.address_title = address.get('address_title')
	add_doc.is_residential = address.get('address_is_residential')
	add_doc.address_contact = address.get('address_contact')
	add_doc.email_id = address.get('address_email_id')
	add_doc.address_line1 = address.get('address_line1')
	add_doc.address_line2 = address.get('address_line2')
	add_doc.phone = address.get('address_phone')
	add_doc.city = address.get('address_city')
	add_doc.state = address.get('address_state')
	add_doc.pincode = address.get('address_zip')
	add_doc.country = address.get('address_country')
	add_doc.flags.ignore_permissions=True
	add_doc.save()
	frappe.db.commit()

def quotation_validate(doc, method):
	main_items = []
	groups = {}

	# Organize items idx for groupping visually
	# find all parent items(not sub groups)
	for item in sorted(doc.items, key=lambda x: x.idx):
		if not item.get("awc_subgroup"):
			main_items.append(item)
			if item.get("awc_group") and not item.get("awc_group") in groups:
				groups[item.get("awc_group")] = []
		else:
			if item.get("awc_group") and not item.get("awc_group") in groups:
				groups[item.get("awc_group")] = []

			if item.get("awc_group"):
				groups[item.get("awc_group")].append(item)

	idx = 1
	for item in main_items:
		item.set("idx", idx)
		idx = idx + 1
		if item.get("awc_group") and item.get("awc_group") in groups:
			for sub_item in groups[item.get("awc_group")]:
				sub_item.set("idx", idx)
				idx = idx + 1

	doc.items = sorted(doc.items, key=lambda x: x.idx)

	return True

@frappe.whitelist()
def is_coupon_valid(coupon_code):
	customer = get_current_customer()
	result = _is_coupon_valid(coupon_code, customer)

	frappe.response["is_coupon_valid"] = result.get("is_valid", False)
	frappe.response["coupon_response_code"] = result.get("code")
	frappe.response["coupon_insert_items"] = result.get("insert_items", [])

	if not result.get("is_valid"):
		return result.get("msg")

	return result.get("label")

@frappe.whitelist(allow_guest=1)
def get_addresses():
	if frappe.session.user != "Guest":
		customer = get_current_customer().name

		address_links = frappe.get_all("Dynamic Link", filters={
			"link_name" : customer,
			"parenttype": "Address",
			"link_doctype": "Customer"},
			fields=["parent"])
		addresses = []
		for address in address_links:
			addresses.extend(frappe.get_all("Address", filters={"name" : address.parent, "disabled" : False}, fields="*"))

		frappe.local.response["addresses"] = addresses
		return True

	return False

def clear_cache_on_doc_update(doc, method):
	clear_cache()

def clear_cache(customer_group=""):
	clear_cache_keys(['*awc-sku*', '*awc-variant*', '*awc-products*'])


def fn_wrap(fn, before_fn):
	"""A fn hot patch helper. Use to wrap method not accesible through hooks or other ways in ERPN.
	Only to be used until the actual functionality is implemented upstream"""

	def _fn(*args, **kwargs):
		try:
			before_fn(*args, **kwargs)
		finally:
			return fn(*args, **kwargs)

	_fn.__patched = True

	return _fn

def erpnext_stock_get_item_details(args):
	"""hot patching for erpnext.stock.get_item_details.get_item_details method
	during item detail setting for quotation, sales order and sales invoices we
	need a way to temporarily turn off price list rules on individual items.

	This method is called on every individual item and we can change the rule behaviour
	by updating passed arg dictionary with the "ignore_pricing_rule" key set to 1.

	This only works because we have a custom field telling us if a user set the
	item_ignore_pricing_rule to 1 on each individual item in the doctype.
	"""

	if args.get("item_ignore_pricing_rule"):
		args["ignore_pricing_rule"] = 1

def boot_session(bootinfo):
	run_hotpatch()

def run_hotpatch(*args, **kwargs):
	from erpnext.stock import get_item_details

	if not hasattr(get_item_details.process_args, "__patched"):
		print(" - Patched: erpnext.stock.get_item_details.process_args -> awesome_cart.utils.erpnext_stock_get_item_details")
		get_item_details.process_args = fn_wrap(get_item_details.process_args, erpnext_stock_get_item_details)

def on_calculate_taxes_and_totals(doc):
	from .taxes_and_totals import AWCCalculateTaxesAndTotals
	AWCCalculateTaxesAndTotals(doc)


def remove_expired_coupons():
	expired_coupons = frappe.get_all("AWC Coupon",
		filters={"autogenerated": 1, "expire_datetime": ["<", frappe.utils.now_datetime()]})

	for coupon in expired_coupons:
		# Try deleting coupon, if it's already linked to an order, simply disable it
		try:
			frappe.delete_doc("AWC Coupon", coupon.name, ignore_permissions=True)
		except frappe.LinkExistsError:
			frappe.db.set_value("AWC Coupon", coupon.name, "enabled", 0)
