from __future__ import unicode_literals

import json
import frappe
from frappe.utils.password import check_password

def is_logged():
	session_user = frappe.get_user()
	user = frappe.get_doc("User", session_user.name)
	
	if user and user.email[-12:] == "@guest.local":
		return False

	return True
	
@frappe.whitelist(allow_guest=True, xss_safe=True)
def login(email, password):
	result = dict(
		success=False,
		msg="Internal Unhandled Error"
	)
	
	try:
		user_doc = check_password(email, password)
		frappe.local.login_manager.login_as(email)
		frappe.set_user(email)

		result["success"] = True
		result["msg"] = ""
	except frappe.AuthenticationError as ex:
		result["success"] = False
		result["msg"] = str(ex)

	return result

@frappe.whitelist(allow_guest=False, xss_safe=True)
def checkout(form):

	result = {
		"success": False,
		"msg": "Not Implemented",
		"errors": {}
	}

	
	

	return result

@frappe.whitelist(allow_guest=True, xss_safe=True)
def register(email, password, password_check, first_name, last_name):
	result = dict(
		success=False,
		msg="Unhandled Error"
	)

	guest_user = frappe.get_user()
	user = frappe.get_doc("User", guest_user.name)
	
	if user:
		if user.email[-12:] == "@guest.local":
			user.email = email
			user.first_name = first_name
			user.last_name = last_name
			user.new_password = password
			user.flags.ignore_permissions = True
			user.save()

			old_name = user.name

			frappe.rename_doc("User", old_name, email, ignore_permissions=True)

			frappe.local.login_manager.login_as(email)
	                frappe.set_user(email)

			contact = frappe.get_doc("Contact", {
				"user": email
			})

			if contact:
				contact.first_name = first_name
				contact.last_name = last_name
				contact.email_id = email
				contact.flags.ignore_permissions = True
				contact.save()

				frappe.rename_doc("Contact", contact.name, email, ignore_permissions=True)

				customer = frappe.get_doc("Customer", contact.customer)

				if customer:
					customer.full_name = "%s %s" % (first_name, last_name)

					customer.flags.ignore_permissions = True
					customer.save()

					frappe.rename_doc("Customer", customer.name, customer.full_name, ignore_permissions=True)

			result["success"] = True
			result["msg"] = ""

		else:
			result["msg"] = "User is not a guest: %s" % user.email
	else:
		result["msg"] = "Internal Error, could not fetch user: %s" % guest_user.name

	return result

def start_checkout():
	pass

def validate_transaction_currency():
	pass
	
