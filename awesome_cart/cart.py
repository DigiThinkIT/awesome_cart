from __future__ import unicode_literals

import json
import frappe

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

	return json.dumps(result)
	
