from __future__ import unicode_literals

import json

import frappe
import frappe.utils
from frappe import _
from frappe.integrations.doctype.ldap_settings.ldap_settings import LDAPSettings
from frappe.utils.oauth import get_oauth2_authorize_url, get_oauth_keys
from frappe.utils.oauth import login_oauth_user as _login_oauth_user
from frappe.utils.oauth import login_via_oauth2, redirect_post_login

__version__ = '7.2.15'


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
