from __future__ import unicode_literals

import json
import traceback
import frappe
from frappe import _dict
from frappe.utils import cint, cstr, random_string, flt
from .dbug import pretty_json, log

def get_awc_session():
	# get session id from request
	sid = frappe.local.session.get("awc_sid", frappe.local.request.cookies.get("awc_sid"))
	if sid:
		awc_sid = "awc_session_{0}".format(sid)
	awc_session = None

	pretty_json(awc_session)

	# lets make sure IPs match before applying this sid
	if sid != None:
		awc_session = frappe.cache().get_value(awc_sid)
		if awc_session:
			if awc_session.get("session_ip") != frappe.local.request_ip:
				# IP do not match... force build session from scratch
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

def clear_awc_session():
	awc_session = get_awc_session()
	del awc_session["shipping_method"]
	del awc_session["shipping_rates"]
	del awc_session["shipping_rates_list"]
	awc_session["cart"] = { "items": [], "totals": { "sub_total": 0, "grand_total": 0, "other": [] } }
