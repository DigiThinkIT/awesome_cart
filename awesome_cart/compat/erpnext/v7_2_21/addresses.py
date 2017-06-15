from __future__ import unicode_literals
import frappe
from erpnext.utilities.doctype.address.address import get_address_display

def create_address(parent_dt, parent,
	address_1, address_2, city, state, pincode, country, email, address_type="Other", title=None, phone=None, return_name=0, flags={}):

	data = {
		"doctype": "Address",
		"address_title": title,
		"address_type": address_type,
		"address_line1": address_1,
		"address_line2": address_2,
		"city": city,
		"state": state,
		"pincode": pincode,
		"country": country,
		"email_id": email,
		"phone": phone
	}

	if parent_dt == "Customer":
		data["customer"] = parent

	doc = frappe.get_doc(data)

	if flags:
		for key, value in flags.iteritems():
			doc.flags[key] = value
		
	doc.insert()

	if return_name:
		return doc.name

	return doc
