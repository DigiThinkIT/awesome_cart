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

def calculate_service_discount(account, coupon_service, state, shipping_info):
	result = 0

	if coupon_service.get("apply_when") == "Is Ground Shipping" and \
		not shipping_info.get("is_ground_shipping"):
		return 0

	amount = account.get("amount", account.get("tax_amount"))
	discount_type = coupon_service.get("discount_type")
	discount_value = coupon_service.get("discount_value")

	if discount_type == "Percentage":
		result = amount * (discount_value / 100.00)
	elif discount_type == "Value Discount":
		result = discount_value

	if result > amount:
		result = amount

	if result < 0:
		result = 0

	if result > 0:
		state.append({ "discount": result, "name": coupon_service.get("discount_label") })

	return result

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
	if amount == 0:
		return 0

	# logic feature only apply discount if another item is present else no
	# discount is calculated
	if coupon_item.apply_logic == "Only If Item B Is Present":
		if coupon_item.item_b_type == "AWC Item Group":
			group_items = frappe.get_all("AWC Coupon Group Item",
				filters={
					"parent": coupon_item.item_b,
					"parenttype": "AWC Item Group"},
				fields=["item_name"],
				as_list=1)

			found = False
			for gitem in group_items:
				item_code = frappe.get_value("Item", gitem[0], "item_code")
				if item_code in item_names:
					found = True
					item_b = item_code

			if not found:
				return 0
		else:
			item_b = frappe.get_value("Item", coupon_item.item_b, "item_code")

			if not item_b in item_names:
				return 0

	result = 0

	if coupon_item.discount_type == "Percent Discount":
		state["item_codes"][item.item_code]["applied_qty"] += item_qty
		result = amount * (coupon_item.discount_value / 100)
	elif coupon_item.discount_type == "Value Discount":
		state["item_codes"][item.item_code]["applied_qty"] += item_qty
		result = coupon_item.discount_value
	elif coupon_item.discount_type == "Actual Value":
		state["item_codes"][item.item_code]["applied_qty"] += item_qty
		result = amount - coupon_item.discount_value
	elif coupon_item.discount_type == "Full Discount":
		state["item_codes"][item.item_code]["applied_qty"] += item_qty
		result = amount

	if result < 0:
		result  = 0

	state["item_codes"][item.item_code]["discount"] += result

	return result

def calculate_coupon_discount(config):

	items = config.get("items")
	coupon_code = config.get("code")
	accounts = config.get("accounts")
	grand_total = config.get("grand_total")
	net_total = config.get("net_total")
	total_limit = False
	msg = None

	shipping_info = {
		"is_ground_shipping": config.get("is_ground_shipping")
	}

	if frappe.db.exists("AWC Coupon", coupon_code):
		coupon_doc = frappe.get_doc("AWC Coupon", coupon_code)
	else:
		return (False, "Coupon Code Not Found", None, None)

	# make quick list of items which this coupon applies to
	coupon_items = []
	coupon_state = { "item_codes": {} }

	def build_item_list(items, item_name):
		item_code = frappe.get_value("Item", item_name, "item_code")
		if not coupon_state.get(item_code):
			coupon_state["item_codes"][item_code] = {
				"cart_qty": 0,
				"applied_qty": 0,
				"name": frappe.get_value("Item", item_name, "item_name"),
				"discount": 0
			}

		for item in items:
			if item.item_code == item_code:
				coupon_state["item_codes"][item_code]["cart_qty"] += item.get("qty", 1)

	# prepopulate item states and build coupon item list
	for citem in coupon_doc.items:
		if citem.item_type == "AWC Item Group":
			group_items = frappe.get_all(
				"AWC Coupon Group Item",
				filters={
					"parent": citem.item_name,
					"parenttype": "AWC Item Group"
				},
				fields=["item_name"],
				as_list=1)

			for gitem in group_items:
				item_code = frappe.get_value("Item", gitem[0], "item_code")
				coupon_items.append({
					"item_code": item_code,
					"item": citem})
				build_item_list(items, item_code)
		else:
			item_code = frappe.get_value("Item", citem.item_name, "item_code")
			coupon_items.append({
				"item_code": item_code,
				"item": citem})
			build_item_list(items, item_code)

	# quick list of items names for logic tests
	item_names = { item.item_code: item for item in items }

	# find all items in doc which coupon applies to
	# then sum their collective discounts and apply to doc
	discount_amount = 0
	for coupon_item in coupon_items:
		discount_amount += sum(
			calculate_item_discount(
				item,
				coupon_item["item"],
				item_names,
				coupon_state
			) for item in items \
				if coupon_item["item_code"] == item.get("item_code")
		)

	discount_state = []
	for key, value in coupon_state.get("item_codes", {}).items():
		# removes 0 discounts states
		if value.get("discount") > 0:
			discount_state.append(value)

	for caccount in coupon_doc.services:
		for account in accounts:
			if account.get("account_head") == caccount.get("account_name"):
				service_discount = calculate_service_discount(
						account,
						caccount,
						discount_state,
						shipping_info)

				discount_amount += service_discount

	# applies total rule if enabled
	if coupon_doc.total_rule == "Total Is Greater Than":
		total_value = net_total if coupon_doc.apply_discount_on == "Net Total" else grand_total - discount_amount
		#total_value -= discount_amount
		discount_value = 0
		discount_label = ""

		if total_value > coupon_doc.total_rule_value:
			if coupon_doc.total_rule_discount_method == "Percent":
				discount_value = (total_value * coupon_doc.total_rule_discount_value) / 100.00
				discount_label = "{0:.0f}% Discount".format(coupon_doc.total_rule_discount_value)
			elif coupon_doc.total_rule_discount_method == "Value":
				discount_value = coupon_doc.total_rule_discount_value
				discount_label = "${:,.2f} Discount".format(discount_value)

			discount_amount += discount_value

			discount_state.append({
				"cart_qty": 1,
				"applied_qty": None,
				"name": discount_label,
				"discount": discount_value
			})
		else:
			# resets discount if total rule doesn't work
			discount_amount = 0
			discount_state = []
			total_limit = True
			msg = "Your cart must be at least ${0} to apply this coupon.".format(coupon_doc.total_rule_value)

	if not msg:
		msg = "Coupon Discount Total: {0}".format(discount_amount),

	return (discount_amount,
		msg,
		coupon_doc.apply_discount_on,
		discount_state,
		True if len(coupon_doc.services) > 0 else False,
		total_limit)

def is_coupon_valid(coupon_code, customer, now=None):
	if not now:
		now = datetime.now()

	if frappe.db.exists("AWC Coupon", coupon_code):
		coupon_doc = frappe.get_doc("AWC Coupon", coupon_code)
	else:
		return {
			"is_valid": False,
			"msg": _("Coupon Code Not Found"),
			"code": "NOT_FOUND"
		}

	# validate enabled field
	if not coupon_doc.enabled:
		return {
			"is_valid": False,
			"msg": _("Coupon Not Found."),
			"code": "NOT_ENABLED"
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
					"group_name": customer.customer_group,
					"coupon_code": coupon_code
				}),
				"code": "GROUP_MISMATCH"
			}

	# validate customer
	if coupon_doc.allowed_customer:
		if not coupon_doc.allowed_customer == customer.name:
			return {
				"is_valid" : False,
				"msg": coupon_doc.customer_mismatch_error.format(**{
					"customer" : customer.name,
					"coupon_code": coupon_code
				})
			}

	# validate enable datetime
	if coupon_doc.enable_datetime:
		if now < coupon_doc.enable_datetime:
			return {
				"is_valid": False,
				"msg": _("Coupon Not Found."),
				"code": "NOT_ENABLED_BY_DATETIME"
			}

	# valdiate expire datetime
	if coupon_doc.expire_datetime:
		if now > coupon_doc.expire_datetime:
			return {
				"is_valid": False,
				"msg": _("Coupon {0} has Expired.").format(coupon_code),
				"code": "EXPIRED"
			}

	# validate per customer use limit
	if coupon_doc.limit_customer_use:
		quotes_total = frappe.db.count("Quotation", filters={"coupon_code": coupon_code, "customer_name": customer.name})
		if quotes_total > coupon_doc.customer_limit:
			return {
				"is_valid": False,
				"msg": _("Coupon Use Limit Reached: {limit}").format(limit=coupon_doc.customer_limit),
				"code": "USE_LIMIT_REACHED"
			}

	items_to_insert = []
	for insert_item in coupon_doc.insert_items:
		items_to_insert.append({
			"sku": frappe.db.get_value("Item", insert_item.item_name, "item_code"),
			"qty": insert_item.qty,
			"lock_qty": insert_item.get("lock_qty", False),
			"total_is_greater_than": insert_item.get("total_is_greater_than", 0)
		})

	return {
		"is_valid": True,
		"msg": "Valid",
		"label": coupon_doc.coupon_label,
		"insert_items": items_to_insert,
		"CODE": "SUCCESS"
	}
