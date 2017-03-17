# -*- coding: utf-8 -*-
# Copyright (c) 2015, DigitThinkIt, Inc. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from datetime import datetime
from awesome_cart.compat.shopping_cart import convert_quotation_to_sales_order
from awesome_cart.compat.accounts import payment_request

LOG_LEVELS = {
	"None": 0,
	"Info": 1,
	"Error": 2,
	"Debug": 3
}

class AWCTransaction(Document):
	def log(self, txt, *args):
		self.data += txt.format(*args) + "\n"

	def on_payment_authorized(self, payment_status):

		quotation = frappe.get_doc("Quotation", this.order_id)
		so = convert_quotation_to_sales_order(quotation)

		preq = payment_request.make_payment_request(dt="Sales Order", dn=so.name, submiti_doc=1, return_doc=1)

		self.reference_doctype = "Payment Request"
		self.reference_docname = preq.name
		self.order_id = so.name
		self.flags.ignore_permissions = 1
		self.save()

		result = preq.run_method("on_payment_authorized", payment_status)

		return result

	def max_log_level(self, level):
		self._max_log_level = LOG_LEVELS[level]

	def log_action(self, data, level):
		if LOG_LEVELS[level] <= self._max_log_level:
			self.append("log",{
				"doctype": "AuthorizeNet Request Log",
				"log": data,
				"level": level,
				"timestamp": datetime.now().strftime("%Y-%d-%m %H:%M:%S")
			})
