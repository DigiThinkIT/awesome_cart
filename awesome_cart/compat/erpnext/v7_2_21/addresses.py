from __future__ import unicode_literals
import frappe
from erpnext.utilities.doctype.address.address import get_address_display

def create_address(parent_dt, parent,
	address_1, address_2, city, state, postal_code, country, address_type="Other", return_name=0):

	data = {
		"doctype": "Address",
		"address_type": address_type,
		"address_line1": address_1,
		"address_line2": address_2,
		"city": city,
		"state": state,
		"pincode": postal_code,
		"country": country
	}

	if parent_dt == "Customer":
		data["customer"] = parent

	doc = frappe.get_doc(data)
	doc.insert()

	if return_name:
		return doc.name

	return doc
