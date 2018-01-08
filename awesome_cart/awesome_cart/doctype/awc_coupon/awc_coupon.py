# -*- coding: utf-8 -*-
# Copyright (c) 2017, DigitThinkIt, Inc. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

from frappe import _
from frappe.model.document import Document
from time import time
from datetime import datetime

class AWCCoupon(Document):
	def validate(self):
		for item in self.items:
			if item.apply_logic == "Only If Item B Is Present" and \
				not item.get("item_b"):
				frappe.throw("Item B Must be defined if using apply logic or item: {0}".format(item.item_name))

def calculate_item_discount(item, coupon_item, item_names, state):

	limit_min = 1
	limit_max = None
	item_qty = item.get("qty", 1)
	if coupon_item.limit_qty == "Limit Individual Items":
		limit_min = coupon_item.limit_qty_min
		limit_max = coupon_item.limit_qty_max
		if item_qty >= limit_min:
			if limit_max:
				if item_qty > limit_max:
					item_qty = limit_max
		else:
			return 0
	elif coupon_item.limit_qty == "Limit All Items":
		limit_min = coupon_item.limit_qty_min
		limit_max = coupon_item.limit_qty_max

		if state["item_codes"][item.item_code]["applied_qty"] >= limit_max:
			return 0

		applicable_qty = state["item_codes"][item.item_code]["cart_qty"] - state["item_codes"][item.item_code]["applied_qty"]

		if applicable_qty >= limit_min:
			if limit_max:
				if applicable_qty > limit_max:
					applicable_qty = limit_max
		else:
			return 0

		if applicable_qty == 0:
			return 0

		if item_qty > applicable_qty:
			item_qty = applicable_qty

	amount = item.get("base_rate", item.get("amount")) * item_qty

	# logic feature only apply discount if another item is present else no
	# discount is calculated
	if coupon_item.apply_logic == "Only If Item B Is Present":
		item_b = frappe.get_value("Item", coupon_item.item_b, "item_code")

		if not item_b in item_names:
			return 0

	if coupon_item.discount_type == "Percent Discount":
		state["item_codes"][item.item_code]["applied_qty"] += item_qty
		return amount * (coupon_item.discount_value / 100)
	if coupon_item.discount_type == "Value Discount":
		state["item_codes"][item.item_code]["applied_qty"] += item_qty
		return coupon_item.discount_value
	if coupon_item.discount_type == "Actual Value":
		state["item_codes"][item.item_code]["applied_qty"] += item_qty
		return amount - coupon_item.discount_value
	if coupon_item.discount_type == "Full Discount":
		state["item_codes"][item.item_code]["applied_qty"] += item_qty
		return amount

	return 0

def calculate_coupon_discount(items, coupon_code):
	if frappe.db.exists("AWC Coupon", coupon_code):
		coupon_doc = frappe.get_doc("AWC Coupon", coupon_code)
	else:
		return (False, "Coupon Code Not Found")

	# make quick list of items which this coupon applies to
	coupon_items = [ {
		"item_code": frappe.get_value("Item", item.item_name, "item_code"),
		"item": item
		} for item in coupon_doc.items ]

	coupon_state = { "item_codes": {} }

	for citem in coupon_doc.items:
		item_code = frappe.get_value("Item", citem.item_name, "item_code")
		if not coupon_state.get(item_code):
			coupon_state["item_codes"][item_code] = {
				"cart_qty": 0,
				"applied_qty": 0
			}

		for item in items:
			if item.item_code == item_code:
				coupon_state["item_codes"][item_code]["cart_qty"] += item.get("qty", 1)

	# quick list of items names for logic tests
	item_names = { item.item_code: item for item in items }

	# find all items in doc which coupon applies to
	# then sum their collective discounts and apply to doc
	discount_amount = 0
	for coupon_item in coupon_items:
		discount_amount += sum(
				calculate_item_discount(
					item, coupon_item["item"],
					item_names, coupon_state
				) for item in items \
					if coupon_item["item_code"] == item.get("item_code")
			)

	return (discount_amount,
		"Coupon Discount Total: {0}".format(discount_amount),
		coupon_doc.apply_discount_on)

def is_coupon_valid(coupon_code, customer, now=None):
	if not now:
		now = datetime.now()

	if frappe.db.exists("AWC Coupon", coupon_code):
		coupon_doc = frappe.get_doc("AWC Coupon", coupon_code)
	else:
		return {
			"is_valid": False,
			"msg": _("Coupon Code Not Found")
		}

	# validate enabled field
	if not coupon_doc.enabled:
		return {
			"is_valid": False,
			"msg": _("Coupon Not Found.")
		}

	# validate customer group filter
	if len(coupon_doc.customer_groups) > 0:
		matched_groups = [ group.customer_group \
			for group in coupon_doc.customer_groups \
				if group.customer_group in (customer.customer_group, "All Customer Groups")
		]

		if len(matched_groups) == 0:
			return {
				"is_valid": False,
				"msg": coupon_doc.customer_groups_mismatch_error.format(**{
					"customer_group": customer.customer_group,
					"coupon_code": coupon_code
				})
			}

	# validate enable datetime
	if coupon_doc.enable_datetime:
		if now < coupon_doc.enable_datetime:
			return {
				"is_valid": False,
				"msg": _("Coupon Not Found.")
			}

	# valdiate expire datetime
	if coupon_doc.expire_datetime:
		if now > coupon_doc.expire_datetime:
			return {
				"is_valid": False,
				"msg": _("This Coupon has Expired.")
			}

	# validate per customer use limit
	if coupon_doc.limit_customer_use:
		quotes_total = frappe.db.count("Quotation", filters={"coupon_code": coupon_code, "customer_name": customer.name})
		if quotes_total > coupon_doc.customer_limit:
			return {
				"is_valid": False,
				"msg": _("Coupon Use Limit Reached: {limit}").format(coupon_doc.customer_limit)
			}

	return {
		"is_valid": True,
		"msg": "Valid",
		"label": coupon_doc.coupon_label
	}
