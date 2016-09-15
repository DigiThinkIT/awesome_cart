from __future__ import unicode_literals
import frappe
import json

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
		for key, value in hook.items():
			plugins[key] = value

	return plugins

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
