# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import os

import frappe
import traceback

from frappe import _
from frappe.utils import random_string

from .dbug import pretty_json


def update_context(context):

	path = frappe.local.request.path[1:]
	context.current_date = ''


def on_session_creation(login_manager):
	pass


def on_logout(login_manager):
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
	add_doc.address_type = "Residential" if address.get('address_type') == "Yes" else "Office"
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