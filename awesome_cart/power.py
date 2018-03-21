from __future__ import unicode_literals

import traceback
import frappe

from .session import get_awc_session, set_awc_session
from .utils import clear_cache
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
			# list all customers this user may make purchases for
			frappe.local.response["customers"] = [{
					"customer_name": x["customer_name"],
					"label": frappe.get_value("Customer", x["customer_name"], "customer_name"),
					"image": frappe.get_value("Customer", x["customer_name"], "image")
				} for x in contacts \
					if ( x.get("can_place_orders") or x.get("is_primary_contact") ) and \
						frappe.get_value("Customer", x["customer_name"], "customer_name")
			]

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
		awc_session["selected_customer"] = customer_name
		set_awc_session(awc_session)

		frappe.db.commit()

		return "Success"

	return "You are NOT allowed to order for this customer"
