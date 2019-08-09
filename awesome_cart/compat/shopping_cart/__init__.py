from __future__ import unicode_literals
import frappe
from frappe import throw, _

from awesome_cart.compat.erpnext.shopping_cart import get_party, \
	apply_cart_settings, set_taxes, get_address_docs, \
	get_applicable_shipping_rules, decorate_quotation_doc, get_shopping_cart_settings

def convert_quotation_to_sales_order(quotation):
	quotation.company = frappe.db.get_value("Shopping Cart Settings", None, "company")
	for fieldname in ["customer_address", "shipping_address_name"]:
		if not quotation.get(fieldname):
			throw(_("{0} is required").format(quotation.meta.get_label(fieldname)))

	quotation.flags.ignore_permissions = True
	quotation.submit()

	if quotation.lead:
		# company used to create customer accounts
		frappe.defaults.set_user_default("company", quotation.company)

	from erpnext.selling.doctype.quotation.quotation import _make_sales_order
	sales_order = frappe.get_doc(_make_sales_order(quotation.name, ignore_permissions=True))
	for item in sales_order.get("items"):
		item.reserved_warehouse = frappe.db.get_value("Item", item.item_code, "website_warehouse") or None

	sales_order.flags.ignore_permissions = True
	sales_order.insert()
	sales_order.submit()
	return sales_order

def get_customer_primary_contact(customer_name):

	# find olddest is_primary or oldest contact
	contacts = frappe.db.sql("""
		SELECT
			c.name as name,
			c.email_id as email_id,
			c.first_name as first_name,
			c.last_name as last_name
		FROM
			`tabContact` c
		LEFT JOIN
			`tabDynamic Link` dl ON dl.parent=c.name
		WHERE
			dl.link_doctype='Customer' AND
			dl.link_name=%(customer_name)s
		ORDER BY 
			c.is_primary_contact DESC,
			c.creation asc
	""", 
	{ "customer_name": customer_name}, 
	as_dict=True)

	# Check if current session user is in the contact list and return that contact info
	for contact in contacts:
		if contact.get("email_id") == frappe.session.user:
			return contact.get("name"), \
				contact.get("email_id"), \
				"%s %s" % (contact.get("first_name", ""), contact.get("last_name", ""))

	# Else, return primary customer contact if one is set
	primary_contact = frappe.db.get_value("Customer", customer_name, "customer_primary_contact")
	if primary_contact:
		return primary_contact, \
			frappe.db.get_value("Contact", primary_contact, "email_id"), \
			"%s %s" % (
				frappe.db.get_value("Contact", primary_contact, "first_name") or "", 
				frappe.db.get_value("Contact", primary_contact, "last_name") or ""
			) 

	# else return first contact on query result
	if len(contacts) > 0:
		return contacts[0].get("name"), \
			contacts[0].get_("email_id"), \
			"%s %s" % (contacts[0].get("first_name", ""), contacts[0].get("last_name", ""))

	frappe.throw("This customer has no primary contact!. Please add one before you continue.")

def _override_get_cart_quotation(party=None):
	if not party:
		party = get_party()

	quotation = frappe.get_all("Quotation", fields=["name"], filters=
		{party.doctype.lower(): party.name, "order_type": "Shopping Cart", "docstatus": 0},
		order_by="modified desc", limit=1, limit_page_length=1)

	contact_person, contact_email, contact_display = get_customer_primary_contact(party.name)

	if quotation:
		qdoc = frappe.get_doc("Quotation", quotation[0].name)
	else:
		qdoc = frappe.get_doc({
			"doctype": "Quotation",
			"naming_series": get_shopping_cart_settings().quotation_series or "QTN-CART-",
			"quotation_to": party.doctype,
			"company": frappe.db.get_value("Shopping Cart Settings", None, "company"),
			"order_type": "Shopping Cart",
			"status": "Draft",
			"contact_display": contact_display,
			"contact_person": contact_person,
			"contact_email": contact_email,
			"customer_name": party.customer_name if party else "",
			"docstatus": 0,
			"__islocal": 1,
			(party.doctype.lower()): party.name
		})

		qdoc.flags.ignore_permissions = True
		qdoc.run_method("set_missing_values")

		apply_cart_settings(party, qdoc)

	contact_modified = False
	if qdoc.contact_person != contact_person:
		frappe.db.set_value("Quotation", qdoc.name, "contact_person", contact_person)
		contact_modified = True

	if qdoc.contact_email != contact_email:
		frappe.db.set_value("Quotation", qdoc.name, "contact_email", contact_email)
		contact_modified = True

	if contact_modified:
		frappe.db.set_value("Quotation", qdoc.name, "contact_display", contact_display)
		qdoc.reload()

	return qdoc

def get_cart_quotation(doc=None, party=None):
	if not party:
		party = get_party()

	if not doc:
		quotation = _override_get_cart_quotation(party)
		doc = quotation

	return {
		"doc": decorate_quotation_doc(doc),
		"addresses": [{"name": address.name, "display": address.display}
			for address in get_address_docs(party=party)],
		"shipping_rules": get_applicable_shipping_rules(party)
	}
