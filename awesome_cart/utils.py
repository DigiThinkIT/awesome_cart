# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import os

import frappe
import traceback

from frappe import _
from frappe.utils import random_string

from .session import clear_awc_session
from .compat.customer import get_current_customer

from dti_devtools.debug import pretty_json, log


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
	add_doc.is_residential = address.get('address_is_residential')
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
def get_addresses():
	if frappe.session.user != "Guest":
		customer = get_current_customer().name
		print(customer)
		frappe.local.response["addresses"] = frappe.get_all("Address", filters={"customer" : get_current_customer().name, "disabled": False}, fields="*")
		return True

	return False
