from __future__ import unicode_literals

import traceback
import frappe

from .session import get_awc_session, set_awc_session, clear_awc_session
from .utils import clear_cache
from .dbug import pretty_json

def get_user_contacts(user):

	if user == "Guest":
		return []

	contacts = frappe.get_all("Contact",
		filters={"user": user},
		fields=["name", "is_primary_contact", "can_place_orders"]
	)

	for contact in contacts:
		contact_links = frappe.get_all("Dynamic Link", filters={
			"parent": contact.get("name"),
			"parenttype": "Contact",
			"link_doctype": "Customer"},
			fields=["link_name"])

		contact["customers"] = [ x.get("link_name") for x in contact_links ]
		# here in case we are using this somewhere else.
		# NOTE: remove once we know we aren't using this
		if len(contact["customers"]) > 0:
			contact["customer_name"] = contact["customers"][0]

	return contacts

@frappe.whitelist(allow_guest=True)
def get_power_user_settings():

	if frappe.session.user == "Guest":
		return "Not A Power User"

	user_doc = frappe.get_doc("User", frappe.session.user)
	frappe.local.response["session_quotation"] = get_awc_session().get("quotation_info", {})

	if user_doc.get("is_power_user")  or \
		has_role([
			"Administrator",
			"Sales User",
			"Sales Manager",
			"System Manager"
		], user_doc.name):

		awc_session = get_awc_session()
		contacts = get_user_contacts(frappe.session.user)

		# pickup selected customer if already selceted
		frappe.local.response["selected_customer"] = awc_session.get("selected_customer")

		if frappe.local.response["selected_customer"]:
			frappe.local.response["selected_customer_image"] = frappe.get_value("Customer", awc_session.get("selected_customer"), "image")
		else:
			frappe.local.response["selected_customer_image"] = None

		frappe.local.response["customers"] = []
		if user_doc.get("is_power_user"):
			frappe.local.response["customers"] = []
			# list all customers this user may make purchases for
			for contact in contacts:
				if contact.get("can_place_orders") or contact.get("is_primary_contact"):
					frappe.local.response["customers"].extend([{
							"customer_name": customer_name,
							"label": frappe.get_value("Customer", customer_name, "customer_name") or customer_name,
							"image": frappe.get_value("Customer", customer_name, "image")
						} for customer_name in contact.get("customers", [])
					])

		return "Power User"

	return "Not A Power User"

def has_role(roles, username):
	if not isinstance(roles, (tuple, list)):
		roles = (roles,)
	roles = set(roles)
	myroles = set(frappe.get_roles(username))

	return roles.intersection(myroles)

@frappe.whitelist()
def set_cart_customer(customer_name):
	user_doc = frappe.get_doc("User", frappe.session.user)

	if user_doc.get("is_power_user") or \
		has_role([
			"Administrator",
			"Sales User",
			"Sales Manager",
			"System Manager"
		], user_doc.name):

		# lets make sure we have a primary contact first
		contact_links = frappe.get_all("Dynamic Link", filters={
			"link_name" : customer_name,
			"link_doctype": "Customer",
			"parenttype": "Contact"},
			fields=["parent"])
		contacts = []
		for contact in contact_links:
			contacts.extend(frappe.get_all("Contact", filters={"name" : contact.parent}, fields="name"))

		if not contacts or len(contacts) == 0:
			return "This Customer requires at least one Contact before placing an order!"

		clear_cache()
		awc_session = get_awc_session()
		clear_awc_session(awc_session)
		awc_session["selected_customer"] = customer_name
		set_awc_session(awc_session)

		frappe.db.commit()

		return "Success"

	return "You are NOT allowed to order for this customer"
