from __future__ import unicode_literals

import json
import traceback
import frappe

from frappe.utils.password import check_password
from erpnext.shopping_cart import cart
from erpnext.accounts.doctype.payment_request import payment_request

from . import dbug
from . import embed

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

		quotation = cart.get_cart_quotation()["doc"]

		user_doc = check_password(email, password)
		frappe.local.login_manager.login_as(email)
		frappe.set_user(email)
		user = frappe.get_doc("User", email)

		# move quotation to logged in user
		quotation.customer = email
		quotation.customer_name = user.customer_name
		quotation.save()

		result["success"] = True
		result["msg"] = ""
		result["user"] = {
			"full_name": user.full_name,
			"name": user.name
		}
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

	try:
		form = json.loads(form)
	except:
		result["msg"] = "Invalid data"
		return result

	dbug.log(json.dumps(form, indent=2))


	billing = form.get("billing", {})
	session_user = frappe.get_user()
	user = frappe.get_doc("User", session_user.name)
	form["user"] = {
		"email": user.email
	}

	try:
		quotation = cart.get_cart_quotation()
		quote = quotation["doc"]
		gateway = embed.get_gateway_module(billing.get("gateway", None))
	except:
		result["success"] = False
		result["msg"] = "Internal Error"
		result["exception"] = traceback.format_exc()

	if gateway:
		
		transaction = create_transaction(quote.grand_total, quote.currency)
		transaction.email = user.email
		
		stored_payment = None
		if form.get("stored_payment", False):
			stored_payment = None # update with new doctype
		
		try:
			success, msg = gateway.process(transaction, form, stored_payment)
			if success:
				result["success"] = True
				# now we'll submit quotation, create sales order,
				# create payment request and fullfill it
				so_name = cart.place_order() # submit quotation and create so

				# lets now create a payment request and fullfill it immediately
				preq = payment_request.make_payment_request(dt="Sales Order", dn=so_name, submiti_doc=1, return_doc=1)

				if preg:
					gdoc = gateway.get_gateway()
					adoc = gateway.get_account()
					gadoc = gateway.get_gateway_account()

					preg.payment_gateway = gdoc.name
					preg.payment_account = adoc.name
					preq.payment_gateway_account = gadoc.name

					preq.flags.ignore_validate_update_after_submit = 1
					preg.save()

					payment_entry = preg.run_method("set_as_paid")

					transaction.data = json.dumps(sanitize_checkout_form(form), indent=4)
					transaction.reference_doctype = "Payment Request"
					transaction.reference_docname = preq.name
					transaction.gateway = gdoc.name
					transaction.save()
					
					frappe.local.response["type"] = "redirect"
					frappe.local.response["location"] = get_url("/cart_success")
			else:
				result["success"] = False
				result["msg"] = msg
		except:
			transaction.data = json.dumps(sanitize_checkout_form(form), indent=4)
			transaction.status = "Failed"
			transaction.transaction_error = transaction.transaction_error or "" 
			transaction.transaction_error += traceback.format_exc() + "\n---\n"
			transaction.save()
			
			result["success"] = False
			result["msg"] = "Internal Error"
			result["exception"] = traceback.format_exc()
		
	
	return result

@frappe.whitelist(allow_guest=True, xss_safe=True)
def register(email, password, password_check, first_name, last_name):
	result = dict(
		success=False,
		msg="Unhandled Error"
	)

	guest_user = frappe.get_user()
	user = frappe.get_doc("User", guest_user.name)
	
	quotation = cart.get_cart_quotation()["doc"]

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

			# move quotation to logged in user
			quotation.customer = email
			quotation.customer_name = user.customer_name
			quotation.save()

			result["success"] = True
			result["msg"] = ""
			result["user"] = {
				"full_name": user.full_name,
				"name": user.name
			}

		else:
			result["msg"] = "User is not a guest: %s" % user.email
	else:
		result["msg"] = "Internal Error, could not fetch user: %s" % guest_user.name

	return result

@frappe.whitelist(allow_guest=True, xss_safe=True)
def start_checkout(amount, currency="USD", date=None):
	validate_transaction_currency(currency)
	
	if not isinstance(data, basestring):
		date = frappe.as_json(data or "{}")

	jdata = json.loads(data)

	if jdata.get("doctype") and jdata.get("docname"):
		reference_doctype = jdata.get("doctype")
		reference_docname = jdata.get("docname")
		reference_doc = frappe.get_doc(reference_doctype, reference_docname)
		
		if reference_doctype == "Payment Request":
			if reference_doc.status not in ["Draft", "Initiated"]:
				frappe.local.response["type"] = "redirect"
				frappe.local.response["location"] = get_url(
				"/orders/{0}".format(reference_doc.reference_name))
				return

		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = get_url("/gateway?name={0}&source={1}".format(reference_docname, reference_doctype))

def sanitize_checkout_form(form):
	if "billing" in form:
		cc = form["billing"]["fields"]["number"]
		form["billing"]["fields"]["number"][-4:].rjust(len(cc), "X")
		code = form["billing"]["fields"]["code"] 
		form["billing"]["fields"]["code"] = "*" * len(code)

def create_transaction(amount, currency, gateway=None, data=None, reference_doc=None):
	transaction = frappe.get_doc({
		"doctype": "AWC Transaction",
		"status": "Initiated",
		"amount": amount,
		"currency": currency,
		"transaction_ref": "-1",
		"data": json.dumps(data or {}),
		"gateway_module": gateway or ""
	});

	if reference_doc:
		transaction.reference_doctype = reference_doc.doctype
		transaction.reference_docname = reference_doc.name

	transaction.insert(ignore_permissions=True)
	frappe.db.commit()

	return transaction

def find_transaction(refence_doc, status="Initiated"):
	transaction = frappe.get_doc("AWC Transaction", {"reference_doctype": ("=", reference_doc.doctype), "reference_docname": ("=", reference_doc.name), "status": status})
	
	return transaction

def validate_transaction_currency(currency):
	if currency not in ["USD"]:
		frappe.throw(
			_("Please select another payment method. '{0}' is unsupported").format(currency)
		)	
	

def transaction_log(gateway_name, data, params=None):
	frappe.get_doc({
		"doctype": "DTI Gateway Log",
		"gateway": gateway_name,
		"error": frappe.as_json(data),
		"params": frappe.as_json(params or "")
	}).insert(ignore_permissions=True)

	return data


