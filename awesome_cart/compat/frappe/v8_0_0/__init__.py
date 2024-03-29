from __future__ import unicode_literals

import json

import frappe
import frappe.contacts.doctype.address.address as addressDocType
import frappe.utils
from frappe import _
from frappe.auth import LoginManager
from frappe.integrations.doctype.ldap_settings.ldap_settings import LDAPSettings
from frappe.utils.oauth import get_oauth2_authorize_url, get_oauth_keys
from frappe.utils.oauth import login_oauth_user as _login_oauth_user
from frappe.utils.oauth import login_via_oauth2, redirect_post_login

__version__ = '8.0.0'


get_address_display = addressDocType.get_address_display

def _customer_fetch_addresses(customer_name, start, limit, order_by, fields, ignore_permissions=False):
	return frappe.get_list("Address",
		fields=fields,
		filters={"customer": customer_name},
		order_by=order_by,
		limit_start=start,
		limit=limit,
		ignore_permissions=ignore_permissions)

def _customer_total_addresses(customer_name):
	return frappe.db.sql("SELECT COUNT(*) FROM tabAddress where customer='{}'".format(customer_name), as_list=1)[0][0];

def login_context(context):
	# get settings from site config
	context.no_header = True
	context.for_test = 'login.html'
	context["title"] = "Login"
	context["disable_signup"] = frappe.utils.cint(frappe.db.get_value("Website Settings", "Website Settings", "disable_signup"))

	for provider in ("google", "github", "facebook", "frappe"):
		if get_oauth_keys(provider):
			context["{provider}_login".format(provider=provider)] = get_oauth2_authorize_url(provider)
			context["social_login"] = True

	ldap_settings = LDAPSettings.get_ldap_client_settings()
	context["ldap_settings"] = ldap_settings

	return context
