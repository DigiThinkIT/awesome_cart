from __future__ import unicode_literals
import frappe
import json
from dbug import log, deprecated

deprecated("""This Module is deprecated from an earlier version of the cart.
			  It is safe to remove once all other references are gone""")
"""
def get_gateway_forms():
	hooks = frappe.get_hooks("awc_setup_gateway_forms") or []
	forms = dict()
	for fn in hooks:
		if isinstance(fn, list):
			for list_fn in fn:
				forms = frappe.get_attr(fn)()
				forms[form["name"]] = form
		else:
			form = frappe.get_attr(fn)()
			forms[form["name"]] = form

	return forms
"""

def get_gateway_plugins():
	hooks = frappe.get_hooks("awc_gateways") or []
	plugins = {}
	for hook in hooks:
		for key, value in hooks.items():
			plugins[key] = {
				'name': key,
				'title': value.get('title')[-1],
				'small_title': value.get('small_title')[-1],
				'supports_stored_payments': value.get('supports_stored_payments', [False])[-1],
				'requires_billing_address': value.get('requires_billing_address', [False])[-1],
				'template': value.get('template')[-1],
				'icon': value.get('icon')[-1]
			}

	log(json.dumps(plugins, indent=2))

	return plugins

def api_get_shipping_rates(items, address):
	hooks = frappe.get_hooks("awc_shipping_api") or {}
	result = []
	for fn in hooks.get("get_rates", []):
		rates = frappe.call(fn, items=items, address=address)
		if isinstance(rates, list):
			result += rates
		elif isinstance(rates, tuple):
			result += list(rates)
		else:
			result += [rates]

	return rates



def get_gateway_module(name):
	gateways = get_gateway_plugins()
	if name in gateways:
		return frappe.get_module("%s.gateway" % name)

	return False

@frappe.whitelist(allow_guest=True, xss_safe=True)
def process_payment(gateway_name, name, source, info):

	#forms = get_gateway_forms()
	plugins = get_gateway_plugins()
	#form = forms.get(gateway_name, None)
	plugin = plugins.get(gateway_name, None)

	if plugin is None:
		return json.dumps({ "success": False, "msg": "Gateway not found" })

	process_fn = frappe.get_attr("%s.gateway.process")

	#return form["process"](name, source, info)
	transaction = None
	fields = {}
	stored_payment = None
	return process_fn(transaction, fields, stored_payment)

def get_stored_payments():
	return []

def has_stored_payments():
	return True

@frappe.whitelist(xss_safe=True)
def get_shipping_rates(address):
	result = {
		"success": False,
		"msg": ""
	}

	rates = api_get_shipping_rates(items = [], address=address)

	for rate in rates:
		rate["currency"] = currency_format(rate["fee"])

	if rates:
		result["rates"] = rates
		result["success"] = True

	return result

def get_cart_currency():
	return "USD"

def currency_format(value):
	return "$%s" % value
