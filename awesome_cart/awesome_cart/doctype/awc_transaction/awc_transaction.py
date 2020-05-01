# -*- coding: utf-8 -*-
# Copyright (c) 2015, DigitThinkIt, Inc. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
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

def call_hook(hook_name, **kwargs):
	hooks = frappe.get_hooks(hook_name) or []
	for hook in hooks:
		# don't allow hooks to break processing
		try:
			frappe.call(hook, **kwargs)
		except Exception:
			# Hook inception, pass exception to hook listening for exception reporting(sentry)
			error_hooks = frappe.get_hooks("error_capture_log") or []
			if len(error_hooks) > 0:
				for error_hook in error_hooks:
					frappe.call(error_hook, async=True)


class AWCTransaction(Document):

	def update_quotation(self):
		quotation = frappe.get_doc("Quotation", self.order_id)
		has_changes = False

		# check if we have a billing address linked
		if self.get('billing_address'):
			if quotation.customer_address != self.billing_address:
				quotation.customer_address = self.billing_address
				has_changes = True
		else:
			# else create one from transaction data
			quotation.customer_address = create_address(
				parent_dt="Customer",
				parent=quotation.customer,
				address_1=self.get("billing_address_1"),
				address_2=self.get("billing_address_2"),
				city=self.get("billing_city"),
				state=self.get("billing_state"),
				pincode=self.get("billing_pincode"),
				country=self.get("billing_country"),
				email=self.get("payer_email"),
				address_type="Billing",
				phone=self.get("billing_phone"),
				title=self.get("billing_title"),
				return_name=1,
				flags={"ignore_permissions": 1}
			)
			has_changes = True

		if quotation.shipping_address_name != self.shipping_address:
			# check if we have a shipping address linked
			quotation.shipping_address_name = self.shipping_address
			has_changes = True

		# assign formatted address text
		if not quotation.shipping_address_name:
			quotation.shipping_address_name = frappe.get_value("AWC Settings", "AWC Settings", "shipping_address")
			has_changes = True

		if quotation.customer_address:
			quotation.address_display = get_address_display(frappe.get_doc("Address", quotation.customer_address).as_dict())
			has_changes = True

		if quotation.shipping_address_name:
			quotation.shipping_address = get_address_display(frappe.get_doc("Address", quotation.shipping_address_name).as_dict())
			has_changes = True

		if has_changes:
			quotation.flags.ignore_permissions = 1
			quotation.save()

		return quotation

	def on_payment_authorized(self, payment_status):
		try:

			# dumb loop to catch out of sync quotation.
			# loop at least 3 times for timestamp error
			tries = 3
			while tries > 0:
				try:
					quotation = self.update_quotation()
					tries = 0 # success, exit loop
				except Exception as ex:
					tries = tries - 1
					if tries <= 0:
						raise ex

			call_hook("awc_transaction_on_payment_authorized", transaction=self, payment_status=payment_status)

			# create sales order
			so = convert_quotation_to_sales_order(quotation)
			self.order_id = so.name

			# let other apps do work after order is generated
			call_hook("awc_transaction_after_on_sales_order_created", transaction=self, order=so)

			if self.flags.get("skip_payment_request", False):
				# avoid TimeStampMismatchError from hook events
				so.reload()
				so.submit()

				self.reference_doctype = "Sales Order"
				self.reference_docname = so.name
			else:
				# then immediately create payment request
				# no emails should be sent as this is intended for immediate fullfilment

				req_type = frappe.local.response.get("type", None)
				req_location = frappe.local.response.get("location", None)

				preq = payment_request.make_payment_request(dt="Sales Order", dn=so.name, submit_doc=1, return_doc=1, mute_email=1)

				#############################################################
				# DIRTY FIX: payment request codebase redirects
				# shopping cart payment requests. Here we are undoing that.
				if req_type:
					frappe.local.response["type"] = req_type
				elif frappe.local.response.get("type"):
					frappe.local.response.pop("type")

				if req_location:
					frappe.local.response["location"] = req_location
				elif frappe.local.response.get("location"):
					frappe.local.response.pop("location")
				#############################################################

				preq.flags.ignore_permissions=1

				if preq.docstatus != 1:
					preq.submit()

				# update transaction record to track payment request record
				self.reference_doctype = "Payment Request"
				self.reference_docname = preq.name

			self.flags.ignore_permissions = 1
			self.save()

			if not self.flags.get("skip_payment_request", False):
				# finally let payment request run its own code to finalize transaction
				# invoice, payment entry docs should be created here
				result = preq.run_method("on_payment_authorized", payment_status)
			else:
				result = None

			# override redirection to orders page
			if result:
				result = '/iems#filter=custom'

			# let other apps do work after order is generated
			call_hook("awc_transaction_finalize", transaction=self, order=so)

			# remove redirect alert on cart generate so's
			if frappe.local.message_log:
				frappe.local.message_log = []

			# don't kill processing if saving cleaning session address info breaks
			try:
				# clears awc session data
				awc.clear_awc_session()
			except Exception as awc_ex:
				pass

			return result
		except Exception as ex:
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
				"timestamp": frappe.utils.now_datetime()
			})
			self.flags.ignore_permissions=1
			self.save()
