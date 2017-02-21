from __future__ import unicode_literals

__version__ = '7.2.21'

import frappe
import erpnext.utilities.doctype.address.address as addressDocType

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
