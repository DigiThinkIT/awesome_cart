# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
import traceback

from frappe import _
from frappe.utils import cint, cstr

class DictCopy:
	def __init__(self, src, dst):
		self.src = src
		self.dst = dst

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.src = None
		self.dst = None

	def copy(self, src_key, dst_key=None):
		if dst_key is None:
			src_key = dst_key

		if src_key in self.src:
			self.dst[dst_key] = self.src[src_key]

def map_address_widget_to_address_doctype(fields, key_prefix=""):
	"""Maps common address widget fields to address doctype fields"""

	result = {}
	with DictCopy(fields, result) as d:
		d.copy(key_prefix + 'address_title', 'address_title')
		d.copy(key_prefix + 'company', 'company')
		d.copy(key_prefix + 'address_1', 'address_line1')
		d.copy(key_prefix + 'address_2', 'address_line2')
		d.copy(key_prefix + 'country', 'country')
		d.copy(key_prefix + 'city', 'city')
		d.copy(key_prefix + 'state', 'pincode')
		d.copy(key_prefix + 'phone', 'phone')

	return result

def get_doctype_next_series(doctype, prefix):
	"""Checks the last series number on doctype name and returns next name.
	This is based on the customer doctype name series for erpnext."""

	count = frappe.db.sql("""select ifnull(max(cast(substring_index(name, ' ', -1) as unsigned)), 0)
			from `tab{0}` where name like '{1} - %'""".format(doctype, prefix), as_list=1)[0][0]
	count = cint(count) + 1
	return "{0} - {1}".format(prefix, cstr(count))

