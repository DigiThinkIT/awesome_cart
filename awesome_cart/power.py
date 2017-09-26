from __future__ import unicode_literals

import traceback
import frappe

from .session import get_awc_session, set_awc_session
from .dbug import pretty_json

def get_user_contacts(user):

	if user == "Guest":
		return []

	contacts = frappe.get_all("Contact",
		filters={"user": user},
		fields=["name", "is_primary_contact", "customer_name", "can_place_orders"]
	)

	return contacts

@frappe.whitelist(allow_guest=True)
def get_power_user_settings():

	if frappe.session.user == "Guest":
		return "Not A Power User"

	user_doc = frappe.get_doc("User", frappe.session.user)

	if user_doc.get("is_power_user") or frappe.session.user == "Administrator":
		awc_session = get_awc_session()
		contacts = get_user_contacts(frappe.session.user)

		# pickup selected customer if already selceted
		frappe.local.response["selected_customer"] = awc_session.get("selected_customer")

		if frappe.local.response["selected_customer"]:
			frappe.local.response["selected_customer_image"] = frappe.get_value("Customer", awc_session.get("selected_customer"), "image")
		else:
			frappe.local.response["selected_customer_image"] = None

		# list all customers this user may make purchases for
		frappe.local.response["customers"] = [{
				"customer_name": x["customer_name"],
				"label": frappe.get_value("Customer", x["customer_name"], "customer_name"),
				"image": frappe.get_value("Customer", x["customer_name"], "image")
			} for x in contacts \
				if x.get("can_place_orders") or x.get("is_primary_contact")
		]

		return "Power User"

	return "Not A Power User"

@frappe.whitelist()
def set_cart_customer(customer_name):
	user_doc = frappe.get_doc("User", frappe.session.user)

	if user_doc.get("is_power_user") or user_doc.name == "Administrator":

		# lets make sure we have a primary contact first
		contact_links = frappe.get_all("Dynamic Link", filters={
			"link_name" : customer_name,
			"link_doctype": "Customer",
			"parenttype": "Contact"},
			fields=["parent"])
		contacts = frappe.get_all("Contact", filters={"customer": customer_name})
		contacts = []
		for contact in contact_links:
			contacts.extend(frappe.get_all("Contact", filters={"name" : contact.parent}, fields="name"))

		if not contacts or len(contacts) == 0:
			return "This Customer requires at least one Contact before placing an order!"

		awc_session = get_awc_session()
		awc_session["selected_customer"] = customer_name
		set_awc_session(awc_session)

		frappe.db.commit()

		return "Success"

	return "You are NOT allowed to order for this customer"
