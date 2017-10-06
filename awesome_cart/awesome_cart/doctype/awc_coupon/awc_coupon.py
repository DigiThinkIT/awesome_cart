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
	pass

def calculate_item_discount(item, coupon_item):
	amount = item.get("base_rate", item.get("amount")) * item.get("qty", 1)

	if coupon_item.discount_type == "Percent Discount":
		return amount * (coupon_item.discount_value / 100)
	if coupon_item.discount_type == "Value Discount":
		return coupon_item.discount_value
	if coupon_item.discount_type == "Actual Value":
		return amount - coupon_item.discount_value
	if coupon_item.discount_type == "Full Discount":
		return amount

	return 0

def calculate_coupon_discount(items, coupon_code):
	if frappe.db.exists("AWC Coupon", coupon_code):
		coupon_doc = frappe.get_doc("AWC Coupon", coupon_code)
	else:
		return (False, "Coupon Code Not Found")

	# make quick list of items which this coupon applies to
	coupon_items = { frappe.get_value("Item", item.item_name, "item_code"): item for item in coupon_doc.items }

	# find all items in doc which coupon applies to
	# then sum their collective discounts and apply to doc
	discount_amount = sum( \
		calculate_item_discount(item, coupon_items[item.get("item_code")]) \
			for item in items \
				if coupon_items.get(item.get("item_code")) )

	return (discount_amount, "Coupon Discount Total: {0}".format(discount_amount), coupon_doc.apply_discount_on)

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

		print(matched_groups)

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
