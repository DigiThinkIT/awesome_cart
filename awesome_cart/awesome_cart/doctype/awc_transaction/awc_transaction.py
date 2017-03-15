# -*- coding: utf-8 -*-
# Copyright (c) 2015, DigitThinkIt, Inc. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from datetime import datetime

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
		result = frappe.get_doc(
			self.reference_doctype,
			self.reference_docname).run_method("on_payment_authorized",
			payment_status)

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
	
