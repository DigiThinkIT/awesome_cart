from __future__ import unicode_literals

import traceback
import frappe

import awc

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

	if user_doc.get("is_power_user"):
		awc_session = awc.get_awc_session()
		contacts = get_user_contacts(frappe.session.user)

		# pickup selected customer if already selceted
		frappe.local.response["selected_customer"] = awc_session.get("selected_customer")

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

	if user_doc.get("is_power_user"):

		awc_session = awc.get_awc_session()
		awc_session["selected_customer"] = customer_name
		awc.set_awc_session(awc_session)

		frappe.db.commit()

		return "Success"

	return "You are NOT allowed to order for this customer"
