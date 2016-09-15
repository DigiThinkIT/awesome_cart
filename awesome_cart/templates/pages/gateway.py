from __future__ import unicode_literals

no_cache = 1
no_sitemap = 1

import frappe
import frappe.website.render
from datetime import date
import urllib
import traceback
import json
from awesome_cart import embed, dbug

def get_context(context):
	#gateway_forms = embed.get_gateway_forms()
	gateway_plugins = embed.get_gateway_plugins()

	name = urllib.unquote(frappe.request.args.get('name', ''))
	source = urllib.unquote(frappe.request.args.get('source', ''))

	countries = []
	awc_countries = frappe.get_all("Awc Country Setting", ["country"])
	for ac in awc_countries:
		country = frappe.get_doc("Country", ac.country)
		countries.append({ "country_name": country.country_name, "code": country.code})

	settings = frappe.db.get("Awc Settings")
	dbug.log(json.dumps(settings, indent=2))
	if settings.default_country:
		if frappe.db.exists("Country", settings.default_country):
			default_country_doc = frappe.get_doc("Country", settings.default_country)
			default_country = default_country_doc.code
		else:
			default_country = None
	else:
		default_country = None


	context.gateway_forms = gateway_plugins
	context.stored_payments = embed.get_stored_payments()
	context.iname = name
	context.isource = source
	context.current_date = dict(year=date.today().year, month=date.today().month, day=date.today().day)
	context.countries = { "countries": countries, "default": default_country }
