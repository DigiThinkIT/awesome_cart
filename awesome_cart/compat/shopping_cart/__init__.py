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

def _override_get_cart_quotation(party=None):
	if not party:
		party = get_party()

	quotation = frappe.get_all("Quotation", fields=["name"], filters=
		{party.doctype.lower(): party.name, "order_type": "Shopping Cart", "docstatus": 0},
		order_by="modified desc", limit=1, limit_page_length=1)

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
			"docstatus": 0,
			"__islocal": 1,
			(party.doctype.lower()): party.name
		})

		if party.doctype.lower() == "customer":
			qdoc.customer_name = party.customer_name

		qdoc.contact_person = frappe.db.get_value("Contact", {"email_id": frappe.session.user,
			"customer": party.name})
		qdoc.contact_email = frappe.session.user

		qdoc.flags.ignore_permissions = True
		qdoc.run_method("set_missing_values")
		apply_cart_settings(party, qdoc)

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
