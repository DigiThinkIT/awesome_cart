from __future__ import unicode_literals

import json
import traceback
import frappe
import hashlib
from frappe import _dict
from frappe.utils import cint, cstr, random_string, flt
from .dbug import pretty_json, log

def get_awc_session():
	# get session id from request
	sid = frappe.local.session.get("awc_sid", frappe.local.request.cookies.get("awc_sid"))
	if sid:
		awc_sid = "awc_session_{0}".format(sid)
	awc_session = None

	# lets make sure IPs match before applying this sid
	if sid != None:
		awc_session = frappe.cache().get_value(awc_sid)
		if awc_session:
			if awc_session.get("session_ip") != frappe.local.request_ip:
				# IP do not match... force build session from scratch
				log(" - AWC Session IP ADDRESS MISTMATCH {0} != {1} ... Resetting\n{2}".format(
					awc_session.get("session_ip"),
					frappe.local.request_ip,
					pretty_json(awc_session)))

				sid = None
				awc_sid = None
				awc_session = None

	if awc_session is None:
		if not sid:
			sid = random_string(64)
			awc_sid = "awc_session_{0}".format(sid)

		awc_session = {
			"session_ip": frappe.local.request_ip,
			"cart": { "items": [], "totals": { "sub_total": 0, "grand_total": 0, "other": [] } }
		}

		frappe.cache().set_value(awc_sid, awc_session)
	else:
		# update old session structures
		if not awc_session.get("cart"):
			awc_session["cart"] = { "items": [], "totals": { "sub_total": 0, "grand_total": 0, "other": [] } }

		if not awc_session["cart"].get("totals"):
			awc_session["cart"]["totals"] = { "sub_total": 0, "grand_total": 0, "other": [] }

		if not awc_session["cart"]["totals"].get("other"):
			awc_session["cart"]["totals"]["other"] = []

	frappe.local.session["awc_sid"] = sid
	frappe.local.cookie_manager.set_cookie("awc_sid", frappe.local.session["awc_sid"] )

	return awc_session

def set_awc_session(session):
	awc_session = get_awc_session()
	frappe.cache().set_value("awc_session_{0}".format(frappe.local.session["awc_sid"]), session)
	return session

def clear_awc_session(awc_session=None, cart_only=False):
	if not awc_session:
		awc_session = get_awc_session()

	if not cart_only:
		if awc_session.get("shipping_method"):
			del awc_session["shipping_method"]
		if awc_session.get("shipping_rates"):
			del awc_session["shipping_rates"]
		if awc_session.get("shipping_rates_list"):
			del awc_session["shipping_rates_list"]
		if awc_session.get("selected_customer"):
			del awc_session["selected_customer"]
		if awc_session.get("selected_customer_image"):
			del awc_session["selected_customer_image"]

	if awc_session.get("timestamp"):
		del awc_session["timestamp"]

	awc_session["cart"] = { "items": [], "discounts": None, "totals": { "sub_total": 0, "grand_total": 0, "other": [] } }

def hash_key(key, prefix=''):
	return prefix + hashlib.sha512(key).hexdigest()

def set_cache(key, value, expires_in_sec=1800, session=None, prefix=''):
	if not session:
		session = get_awc_session()
	sid = frappe.local.session["awc_sid"]

	frappe.cache().set_value(key=hash_key(key, prefix), val=value, user=sid, expires_in_sec=expires_in_sec)

def get_cache(key, expires=False, session=None, prefix=''):
	if not session:
		session = get_awc_session()

	sid = frappe.local.session["awc_sid"]

	return frappe.cache().get_value(key=hash_key(key, prefix), user=sid, expires=expires)

def clear_cache_keys(keys):
	if not isinstance(keys, list):
		keys = [keys]

	for key in keys:
		frappe.cache().delete_keys(key)

def get_quick_cache(key, awc_session=None, customer=None, prefix=None):

	if not prefix:
		prefix = "awc-sku-{}"

	if not awc_session:
		awc_session = get_awc_session()
	
	if not customer:
		from compat.customer import get_current_customer
		customer = get_current_customer()

	customer_lbl = "None"
	if customer:
		customer_lbl = customer.customer_group

	cache_prefix = prefix.format(customer_lbl)
	cache_data = get_cache(key, session=awc_session, prefix=cache_prefix)

	return cache_data, cache_prefix, awc_session

