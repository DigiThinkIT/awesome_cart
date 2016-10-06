# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import os

import frappe
import traceback

from frappe import _
from frappe.utils import random_string
from .dbug import log, json_default
from .cart import start_checkout, validate_transaction_currency

def on_render_page(path):
        log("-- on render_page(%s)" % path)
        try:
            filepath, ext = os.path.splitext(path)
            # we only care about pages
            if ext not in [".js", ".css"]:
                user = frappe.get_user()
                if user.name == "Guest":
                    rnd = random_string(20)
                    email = rnd + "@guest.local"
                    user = frappe.get_doc({
                        "doctype": "User",
                        "email": email,
			"name": rnd,
                        "first_name": "Guest",
                        "enabled": 1,
                        "new_password": random_string(10),
                        "user_type": "Website User"
                    })
                    user.flags.ignore_permissions = True
                    user.insert()
                    frappe.local.login_manager.login_as(user.name)
                    frappe.set_user(user.name)

                log("USER: %s" % user.name)
	except Exception as exp:
		log(traceback.format_exc())


def update_context(context):

	path = frappe.local.request.path[1:]
	log("Path: %s" % frappe.local.request.path)

	context.current_date = ''

	#if path == 'cart':
	#	from .templates.pages import cart
	#	cart.get_context(context)
	#
	#	log("Context for: \n%s" % json.dumps(context, indent=2, default=json_default))

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

def get_payment_url(doc, method):
	if doc.status == 1:
		start_checkout(doc.grand_total, doc.currency, {
			"doctype": doc.doctype,
			"docname": doc.name})
		frappe.respond_as_web_page(
			_("Invalid Payment Gateway Request: %s" % doc.docstatus),
			_("Payment Request has been canceled."),
			success=False,
			http_status_code=frappe.ValidationError.http_status_code)

def validate_price_list_currency(doc, method):
	if doc.enabled and doc.enable_checkout:
		if not doc.payment_gateway_account:
			doc.enable.checkout = 0
