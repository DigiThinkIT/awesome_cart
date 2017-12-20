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

from dti_devtools.debug import log, pretty_json

# simple log level translation table to match ints
LOG_LEVELS = {
	"None": 0,
	"Info": 1,
	"Error": 2,
	"Debug": 3
}

class AWCTransaction(Document):

	def on_payment_authorized(self, payment_status):
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
					pincode=self.get("billing_pincode"),
					country=self.get("billing_country"),
					email=self.get("payer_email"),
					address_type="Billing",
					phone=self.get("billing_phone"),
					title=self.get("billing_title"),
					return_name=1,
					flags={"ignore_permissions": 1}
				)

			# check if we have a shipping address linked
			quotation.shipping_address_name = self.shipping_address

			# assign formatted address text
			if not quotation.shipping_address_name:
				quotation.shipping_address_name = frappe.get_value("AWC Settings", "AWC Settings", "shipping_address")

			quotation.address_display = get_address_display(frappe.get_doc("Address", quotation.customer_address).as_dict())
			quotation.shipping_address = get_address_display(frappe.get_doc("Address", quotation.shipping_address_name).as_dict())

			quotation.flags.ignore_permissions = 1
			quotation.save()

			# create sales order
			so = convert_quotation_to_sales_order(quotation)

			if self.flags.get("skip_payment_request", False):
				so.submit()
				# NOTE: TEST THIS!!!! WHY IS THERE A SAVE AFTER SUBMIT???????
				#so.save()

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
				# preq.insert()

				log(preq)

				if preq.docstatus != 1:
					preq.submit()

				# update transaction record to track payment request record
				self.reference_doctype = "Payment Request"
				self.reference_docname = preq.name

			self.order_id = so.name
			self.flags.ignore_permissions = 1
			self.save()

			if not self.flags.get("skip_payment_request", False):
				# finally let payment request run its own code to finalize transaction
				# invoice, payment entry docs should be created here
				result = preq.run_method("on_payment_authorized", payment_status)
			else:
				result = None

			# update shipping method in Sales Order
			#if self.get("shipping_method"):
			#	frappe.db.set_value("Sales Order", self.order_id, "fedex_shipping_method", self.get("shipping_method"))

			if self.get("gateway_service"):
				has_universals = False
				for item in frappe.get_doc("Sales Order", self.order_id).items:
					if frappe.db.get_value("Item", item.item_code, "item_group") == "Universal":
						has_universals = True
				if self.get("gateway_service") == "credit_gateway":
					frappe.db.set_value("Sales Order", self.order_id, "payment_method", "Bill Me")
				elif self.get("gateway_service") == "paypal":
					frappe.db.set_value("Sales Order", self.order_id, "payment_method", "PayPal")
					frappe.db.set_value("Sales Order", self.order_id, "authorize_production", False)
					frappe.db.set_value("Sales Order", self.order_id, "authorize_delivery", False)
				else:
					if self.get("gateway_service") == "authorizenet":
						frappe.db.set_value("Sales Order", self.order_id, "payment_method", "Card")
					else:
						frappe.db.set_value("Sales Order", self.order_id, "payment_method", self.get("gateway_service"))

					if not has_universals:
						frappe.db.set_value("Sales Order", self.order_id, "authorize_production", True)
						frappe.db.set_value("Sales Order", self.order_id, "authorize_delivery", True)

			# override redirection to orders page
			if result:
				result = '/iems#filter=custom'

			# this is here to remove duplication warning messages.
			# TODO: Consider bring this to erpnext team to remove warning
			if frappe.local.message_log:
				for msg in frappe.local.message_log:
					self.log_action(msg, "Info")
				frappe.local.message_log = []

			# don't kill processing if saving cleaning session address info breaks
			try:
				# clears awc session data
				awc.clear_awc_session()
			except Exception as awc_ex:
				log(frappe.get_traceback())
				self.log_action(frappe.get_traceback(), "Error")
				pass

			return result
		except Exception as ex:
			log(frappe.get_traceback())
			self.log_action(frappe.get_traceback(), "Error")
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
