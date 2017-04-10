# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
import traceback

from frappe import _
from frappe.utils import cint, cstr
from .dbug import deprecated
#from frappe.geo.doctype.address.address import get_address_display

deprecated("""This Module is deprecated from an earlier version of the cart.
			  It is safe to remove once all other references are gone""")

class DictCopy:
	def __init__(self, src, dst):
		self.src = src
		self.dst = dst

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.src = None
		self.dst = None

	def copy(self, src_key, dst_key=None, copy_none=True):
		if dst_key is None:
			src_key = dst_key

		if src_key in self.src:
			copy = True
			if self.src[src_key] is None and not copy_none:
				copy = False

			if copy:
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
		d.copy(key_prefix + 'state', 'state')
		d.copy(key_prefix + 'zip', 'pincode')
		d.copy(key_prefix + 'phone', 'phone')

	return result

def get_doctype_next_series(doctype, prefix):
	"""Checks the last series number on doctype name and returns next name.
	This is based on the customer doctype name series for erpnext."""

	count = frappe.db.sql("""select ifnull(max(cast(substring_index(name, ' ', -1) as unsigned)), 0)
			from `tab{0}` where name like %s""".format(doctype), '%s - %%' % prefix, as_list=1)[0][0]
	count = cint(count) + 1
	return "{0} - {1}".format(prefix, cstr(count))

def transfer_quotation_to_user(quotation, user, customer = None, contact = None):
	if not customer:
		customer = find_user_customer(user)

	if not contact:
		contact = find_user_primary_contact(user)

	quotation.customer = customer.name
	quotation.customer_name = customer.customer_name
	quotation.contact_person = contact.name
	quotation.title = "Shopping Cart - %s" % quotation.customer_name
	quotation.contact_email = contact.email_id
	quotation.owner = user.name
	quotation.contact_display = customer.customer_name
	quotation.flags.ignore_permissions = True
	quotation.save()

def find_user_primary_contact(user, or_any_available=True):
	"""Finds the first primary contact linked to this user"""
	contacts = get_contacts("user", user.name)

	if not or_any_available:
		if not contacts[0].get("is_primary_contact", False):
			return None

	if contacts:
		return contacts[0]

	return None

def find_user_customer(user):
	"""Finds the first customer linked to this user"""
	contact = find_user_primary_contact(user)

	if contact:
		customer = frappe.get_doc("Customer", contact.customer)
		return customer

	return None

def get_contacts(key, value):
	"""Simple generic search for contacts based on a 'key' field and value"""
	return frappe.get_all("Contact", fields="*", filters={key: value},
		order_by="is_primary_contact desc, modified desc")

def get_addresses(key, value):
	"""Simple generic search for addresses based on a 'key' field and value"""
	return frappe.get_all("Address", fields="*", filters={key: value},
		order_by="is_primary_address desc, modified desc")
