# -*- coding: utf-8 -*-
# Copyright (c) 2015, DigitThinkIt, Inc. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from datetime import datetime
from awesome_cart.compat.shopping_cart import convert_quotation_to_sales_order
from awesome_cart.compat.accounts import payment_request
from awesome_cart.compat.addresses import get_address_display, create_address

from awesome_cart import awc

# simple log level translation table to match ints
LOG_LEVELS = {
	"None": 0,
	"Info": 1,
	"Error": 2,
	"Debug": 3
}

class AWCTransaction(Document):
	def on_payment_authorized(self, payment_status):
		# clears awc session data
		awc.clear_awc_session()

		try:
			quotation = frappe.get_doc("Quotation", self.order_id)

			# check if we have a billing address linked
			if self.get('billing_address'):
				quotation.customer_address = self.billing_address
			else:
				# else create one from transaction data
				quotation.customer_address = create_address(
					parent_dt="Customer",
					parent=quotation.customer,
					address_1=self.get("billing_address_1"),
					address_2=self.get("billing_address_2"),
					city=self.get("billing_city"),
					state=self.get("billing_state"),
					postal_code=self.get("billing_postal_code"),
					country=self.get("billing_country"),
					return_name=1
				)

			# check if we have a shipping address linked
			if self.get('shipping_address'):
				quotation.shipping_address_name = self.shipping_address
			else:
				# else create one from transaction data
				quotation.shipping_address_name = create_address(
					parent_dt="Customer",
					parent=quotation.customer,
					address_1=self.get("shipping_address_1"),
					address_2=self.get("shipping_address_2"),
					city=self.get("shipping_city"),
					state=self.get("shipping_state"),
					postal_code=self.get("shipping_postal_code"),
					country=self.get("shipping_country"),
					return_name=1
				)

			# assign formatted address text
			quotation.address_display = get_address_display(frappe.get_doc("Address", quotation.customer_address).as_dict())
			quotation.shipping_address = get_address_display(frappe.get_doc("Address", quotation.shipping_address_name).as_dict())
			quotation.save()

			# create sales order
			so = convert_quotation_to_sales_order(quotation)

			# then immediately create payment request
			# no emails should be sent as this is intended for immediate fullfilment
			preq = payment_request.make_payment_request(dt="Sales Order", dn=so.name, submit_doc=1, return_doc=1, mute_email=1)
			preq.insert()

			# update transaction record to track payment request record
			self.reference_doctype = "Payment Request"
			self.reference_docname = preq.name
			self.order_id = so.name
			self.flags.ignore_permissions = 1
			self.save()

			# finally let payment request run its own code to finalize transaction
			# invoice, payment entry docs should be created here
			result = preq.run_method("on_payment_authorized", payment_status)

			# this is here to remove duplication warning messages.
			# TODO: Consider bring this to erpnext team to remove warning
			if frappe.local.message_log:
				for msg in frappe.local.message_log:
					self.log_action(msg, "Info")
				frappe.local.message_log = []

			return result
		except Exception as ex:
			print(frappe.get_traceback())
			self.log_action(frappe.get_traceback(), "Debug")
			raise ex

	def max_log_level(self, level):
		self._max_log_level = LOG_LEVELS[level]

	def log_action(self, data, level):

		# load default log level if one was not set earlier
		if not hasattr(self, "_max_log_level"):
			self.max_log_level(frappe.db.get_value("Awc Settings", fieldname="log_level"))

		if LOG_LEVELS[level] <= self._max_log_level:
			self.append("log", {
				"doctype": "AWC Transaction Log",
				"log": data,
				"level": level,
				"timestamp": datetime.now().strftime("%Y-%d-%m %H:%M:%S")
			})
			self.save()
