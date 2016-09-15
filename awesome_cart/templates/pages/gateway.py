from __future__ import unicode_literals

no_cache = 1
no_sitemap = 1

import frappe
import frappe.website.render
from datetime import date
import urllib
import traceback
from awesome_cart import embed, dbug

def get_context(context):
	gateway_forms = embed.get_gateway_forms()
	name = urllib.unquote(frappe.request.args.get('name', ''))
	source = urllib.unquote(frappe.request.args.get('source', ''))

	context.gateway_forms = gateway_forms
	context.stored_payments = embed.get_stored_payments()
	context.iname = name
	context.isource = source
	context.current_date = dict(year=date.today().year, month=date.today().month, day=date.today().day)
