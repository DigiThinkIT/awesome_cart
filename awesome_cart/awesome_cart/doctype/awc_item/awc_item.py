# -*- coding: utf-8 -*-
# Copyright (c) 2015, DigitThinkIt, Inc. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from awesome_cart.utils import clear_cache

class AWCItem(Document):

	def on_update(self):
		clear_cache()
