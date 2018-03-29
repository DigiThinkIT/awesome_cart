# -*- coding: utf-8 -*-
# Copyright (c) 2015, DigitThinkIt, Inc. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from erpnext.setup.setup_wizard.operations.company_setup import create_bank_account

class AwcSettings(Document):
	def on_update(self):
		setup_gateway("Awesome Cart", self.awc_enabled)

def create_gateway(name):
	"""Creates a gateway using the provided name"""

	if not frappe.db.exists("Payment Gateway", name):
		gateway = frappe.get_doc({
			"doctype": "Payment Gateway",
			"gateway": name
		});
		gateway.insert(ignore_permissions=True)

		return gateway
	else:
		gateway = frappe.get_doc("Payment Gateway", name)

		return gateway

def create_gateway_bank_account(name):
	"""Creates a gateway bank account of the same name"""

	company = frappe.db.get_value("Global Defaults", None, "default_company")

	if not company:
		return

	account = frappe.db.get_value(
		"Account",
		{"account_name": _(name), "company": company},
		["name", "account_currency"],
		as_dict=True)

	if not account:
		account = frappe.db.get_value(
			"Account",
			{"account_name": name, "company": company},
			["name", "account_currency"],
			as_dict=True)

	if not account:
		account = create_bank_account({
			"company_name": company,
			"bank_account": _(name)
		})

	if not account:
		frappe.msgprint(_("Payment Gatway '{0}' was not created. Please create one manually.".format(name)))
		return None

	return account

def create_gateway_account(name, bank_account):
	"""Create gateway account for gateway of same name"""

	currency = frappe.db.get_value("Global Defaults", None, "default_currency")
	if not frappe.db.exists("Payment Gateway Account", {
			"payment_gateway": name,
			"currency": bank_account.get("account_currency", currency)}):

		account = frappe.get_doc({
			"doctype": "Payment Gateway Account",
			"is_default": 0,
			"payment_gateway": name,
			"payment_account": bank_account.name,
			"currency": bank_account.get("account_currency", currency)})

		account.insert(ignore_permissions=True)
		return account
	else:
		account = frappe.get_doc("Payment Gateway Account",
			{"payment_gateway": name, "currency": bank_account.account_currency})

		return account


def setup_gateway(gateway_name, enable):
	"""Builds gateway, account, bank account and default settings"""

	if "erpnext" not in frappe.get_installed_apps():
		return

	if gateway_name is None:
		raise Exception("Gateway name was empty")

	gateway = create_gateway(gateway_name)

	bank_account = create_gateway_bank_account(gateway_name)
	if bank_account:
		gateway_account = create_gateway_account(gateway_name, bank_account)
