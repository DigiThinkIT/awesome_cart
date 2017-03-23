from __future__ import unicode_literals

import json
import traceback
import frappe
from frappe import _dict
from frappe.utils import cint, cstr
from erpnext.stock.get_item_details import apply_price_list_on_item
from erpnext.shopping_cart.product import get_product_info

from compat.customer import get_current_customer
from compat.shopping_cart import get_cart_quotation, apply_cart_settings

def find_index(arr, fn):
	for i, item in enumerate(arr):
		if fn(item):
			return i

	return -1

def get_template(tpl_name):
	"""Get the template by name"""
	if tpl_name and frappe.db.exists("AWC Template", tpl_name):
	   tpl = frappe.get_doc("AWC Template", tpl_name)
	   return tpl.get("template_body", "")

	return ""

def get_awc_item_by_route(route):
	"""Retrieves awc item by its route"""
	# Get awc item name through a get_list and filter call
	# then query the actual doctype with name.
	# NOTE: Is there a less convoluted way of searching doctypes and getting
	#       it's doctype instance?
	awc_item = frappe.get_list("AWC Item", fields="name", filters = {"product_route": route}, ignore_permissions=1)
	awc_item = frappe.get_doc("AWC Item", awc_item[0].name)

	# Finally get the item associated with this AWC item
	item = frappe.get_doc("Item", awc_item.product_name)

	# return both as they are usually used together
	return (awc_item, item)

def get_awc_item_custom_data(name):
	"""Returns a dictionary of custom key/values in the awc item"""
	if isinstance(name, str) or isinstance(name, unicode):
		awc_item = frappe.get_doc("AWC Item", name)
	else:
		awc_item = name

	custom_data = {}
	for custom in awc_item.get("custom_data"):
		custom_data[custom.key] = custom.value

	return custom_data

def build_awc_options_from_varients(item):

	item = frappe.get_doc("Item", item.name)

	context = _dict()
	context = item.get_context(context)

	options = {'variants': [], 'hashes': {}}
	if item.get('has_variants'):

		for att in item.get('attributes'):
			attribute = frappe.get_doc('Item Attribute', att.get('attribute'))

			values = context.get('attribute_values')[attribute.attribute_name]

			options['variants'].append({
				'id': attribute.name,
				'label': attribute.attribute_name,
				'values': values,
				'default': context.get('selected_attributes').get(attribute.name)
			})

		for variant in context.get('variants'):
			tmp_atts = dict()
			for att in variant.get('attributes', []):
				att_name = att.get('attribute')
				att_value = att.get('attribute_value')
				tmp_atts[att_name] = att_value

			opt_hash = []
			for opt_variant in options['variants']:
				opt_hash.append(tmp_atts.get(opt_variant.get('id')))


			options["hashes"][",".join(opt_hash)] = variant.get('name')

	return options

def get_content_sections(awc_item):
	"""Returns and groups content by it's leading section"""
	sections = []
	section = None
	for content in awc_item.get("product_content"):
		if content.data_type == "Section Break":
			# when we find a section add last section to section list
			if section:
				sections.append(section)

			# fill out section values
			section = { "content": [], "background_image_url": content.get("background_image_url") }

		else:
			# create section object if none are set. This makes it a default section
			if not section:
				section = { "content": [] }

			# by default we should always expect at least one content piece
			section_content = { "html": [content.data_content_1] }

			# check if we want more than one content pice
			if cint(content.data_content_count) > 1:
				# then add it to our content array
				section_content["html"].append(content.data_content_2)

			# finally add this content object to the section
			section["content"].append(section_content)

	# if we have one section left, add it to the sections list
	if section:
		sections.append(section)

	return sections

@frappe.whitelist(allow_guest=True, xss_safe=True)
def get_product_by_sku(sku, detailed=0):
	"""Get's product in awcjs format by its sku and optionally detailed data."""
	# fetch item by its sku/item_code
	item = frappe.get_list("Item", fields="*", filters = {"item_code": sku}, ignore_permissions=1)[0]
	# get item price list information
	_item = _dict(get_product_info(item.item_code))
	# get awc item name by its item link
	awc_item = frappe.get_list("AWC Item", fields="*", filters = {"product_name": item.name}, ignore_permissions=1)[0]
	# finally get awc_item doctype instance
	awc_item = frappe.get_doc("AWC Item", awc_item.name)
	# get awc_item custom data as dictionary
	custom_data = get_awc_item_custom_data(awc_item)

	# format product for awcjs
	product = dict(
		sku=item.name,
		name=item.name,
		custom=custom_data,
		warehouse=item.get("default_warehouse"),
		description=awc_item.description_short,
		imageUrl=awc_item.product_thumbnail,
		productUrl="/p/%s" % awc_item.product_route,
		price=_item.get("price.price_list_rate", item.get("standard_rate", "[[ERROR MISSING RATE]]")),
		listing_widget=awc_item.listing_widget,
		product_widget=awc_item.product_widget,
		product_template=awc_item.product_template,
		options=build_awc_options_from_varients(item),
		tags=awc_item._user_tags.split(',') if awc_item._user_tags else []
	)

	# append detailed information only if required
	if detailed:
		product["detail"] = dict(
			description_short=awc_item.description_short,
			description_long=awc_item.description_long,
			sections=get_content_sections(awc_item)
		)

	return { "success": True, "data": product }

@frappe.whitelist(allow_guest=True, xss_safe=True)
def fetch_products(tags="", terms="", order_by="order_weight", order_dir="asc", start=0, limit=9):
	"""Fetches a list of products filtered by tags"""

	payload = {
		"success": False
	}
	try:
		tags = tags.split(',')  # split tag string into list
		# Convert order_by and order_dir values to acceptable values or defaults
		order_by_clean = dict(weight="order_weight").get(order_by if order_by else "", "order_weight")
		order_dir_clean = dict(asc="asc", desc="desc").get(order_dir if order_dir else "", "asc")

		# builds the WHERE part of the sql query to match tags by AND/OR binary matches
		# matches are grouped into groups of AND matches with extra groups being OR
		# example:
		# ( tagmatch AND tagmatch AND tagmatch ) OR ( tagmatch AND tagmatch AND tagmatch )
		tags_match = []
		tag_group = []
		for tag in tags:
			if tag:
				# anything prepended with a pipe is an OR match
				if tag[0] == '|':
					if len(tag_group) > 0:
						tags_match.append(tag_group)
						tag_group = []
					tag_group.append(' a._user_tags REGEXP "(^|,){}(,|$)" '.format(tag[1:]))
				else: # anything else is an AND match
					tag_group.append(' a._user_tags REGEXP "(^|,){}(,|$)" '.format(tag))

		# add any dangly groups to match list
		if len(tag_group) > 0:
			tags_match.append(tag_group)

		# build actual WHERE query part from groups
		if len(tags_match) > 0:
			tags_match = " OR ".join( \
				["({})".format(" AND ".join(group)) \
					for group in tags_match]
			)
			if tags_match:
				tags_match = "({})".format(tags_match)

		else:
			tags_match = ""

		sql_count = "SELECT count(*) \
			FROM `tabAWC Item` a\
			{};\
			".format("WHERE %s" % tags_match if tags_match else "")

		result_count = cint(frappe.db.sql(sql_count, as_list=1)[0][0])

		sql = """SELECT
			i.name,
			i.item_code,
			i.has_variants,
			i.standard_rate,
			a.name as awc_item_name,
			a.product_route as awc_product_route,
			a.description_short as awc_description_short,
			a.description_long as awc_description_long,
			a.listing_widget as awc_listing_widget,
			a.product_widget as awc_product_widget,
			a.product_template as awc_product_template,
			a.product_thumbnail as awc_product_thumbnail,
			a.slider as awc_slider,
			a._user_tags as awc_tags
			FROM `tabAWC Item` a, `tabItem` i
			WHERE i.name = a.product_name
			AND a.catalog_visible=1
			{}
			ORDER BY {} {}
			LIMIT {}, {}""".format(
				"AND %s" % tags_match if tags_match else "",
				order_by_clean,
				order_dir_clean,
				int(start),
				int(limit))

		result = frappe.db.sql(sql, as_dict=1)

		products = []
		for item in result:
			_item = _dict(get_product_info(item.item_code))
			product = dict(
				sku=item.name,
				name=item.name,
				custom=get_awc_item_custom_data(item.awc_item_name),
				productUrl="/p/%s" % item.awc_product_route,
				description=item.awc_description_short,
				imageUrl=item.awc_product_thumbnail,
				price=_item.get("price.price_list_rate", item.get("standard_rate", "[[ ERROR MISSING RATE]]")),
				listing_widget=item.awc_listing_widget,
				product_widget=item.awc_product_widget,
				product_template=item.awc_product_template,
				options=build_awc_options_from_varients(item),
				tags=item.awc_tags.split(',') if item.awc_tags else []
			)
			products.append(product)

		payload["success"] = True
		payload["total_records"] = result_count
		payload["data"] = products
	except Exception as ex:
		payload["success"] = False
		payload["message"] = traceback.format_exc(ex)
		print(payload["message"])

	return payload

def collect_totals(quotation, awc):
	awc["totals"]["sub_total"] = quotation.get("total")
	awc["totals"]["grand_total"] = quotation.get("grand_total")

def get_awc_session_id():
	return '%s_awc_cart' % frappe.local.session.sid

def get_awc_session():
	sid = get_awc_session_id()
	awc = frappe.cache().get_value(sid)
	return awc

def set_awc_session(awc):
	sid = get_awc_session_id()
	frappe.cache().set_value(sid, awc)

def clear_awc_session():
	awc = { "items": [], "totals": { "sub_total": 0, "grand_total": 0 } }
	set_awc_session(awc)
	return awc

def sync_awc_and_quotation(awc, quotation):
	# convert quotation to awc object
	# and merge items in the case where items are added before logging in.

	# steps:
	# 1) loop over all awc items and update quotation items matching names/ids
	# 2) remove invalid awc items who's skus do not match any products(awc items)
	# 3) loop over remaining unmatched quotation items and create awc items
	# 4) remove invalid quotation items who's skus do not match any products(awc items)

	quotation_is_dirty = False
	awc_is_dirty = False
	awc_items_to_remove = []
	awc_items_matched = []
	# step 1
	# iterate over all awc items and update quotation to match values
	awc_items = awc.get("items", [])
	for awc_idx in range(0, len(awc_items)):
		awc_item = awc_items[awc_idx]
		idx = find_index(quotation.get("items", []), lambda itm: itm.get("name") == awc_item.get("id"))
		product = get_product_by_sku(awc_item.get("sku"))

		if awc_item.get("id"):
			if idx > -1:
				item = quotation.items[idx]
				# make sure product exists
				if product.get("success"):
					product = product.get("data")
					if item.qty != awc_item.get("qty"):
						item.qty = awc_item.get("qty")
						quotation_is_dirty = True

					if item.item_code != awc_item.get("sku"):
						item.item_code = awc_item.get("sku")
						quotation_is_dirty = True

					item.warehouse = product.get("warehouse")

					awc_items_matched.append(awc_item.get("id"))
				else:
					# sku is invalid. Flag item to be removed from awc session
					awc_items_to_remove.append(awc_item)
			else:
				if product.get("success"):
					product = product.get("data")
					# no quotation item matched, so lets create one
					quotation.append("items", {
						"doctype": "Quotation Item",
						"item_code": awc_item.get("sku"),
						"qty": awc_item.get("qty"),
						"warehouse": product.get("warehouse")
					})
					quotation_is_dirty = True
				else:
					awc_items_to_remove.append(awc_item)
		else:
			# drop awc items if they have invalid ids
			awc_items_to_remove.append(awc_item)

	# step 2
	# remove invalid awc items
	for awc_item in awc_items_to_remove:
		idx = awc["items"].index(awc_item)
		del awc["items"][idx]
		awc_is_dirty = True

	quotation_item_to_remove = []
	# step 3
	# now create awc items for quotation items not matched with existing awc session
	for item in [qitem for qitem in quotation.get("items", []) \
		if qitem.name not in awc_items_matched]:

		product = get_product_by_sku(item.get("item_code"))
		if product.get("success"):
			product = product.get("data")
			awc_item = {
				"id": item.name,
				"sku": item.item_code,
				"qty": item.qty,
				"warehouse": product.get("warehouse")
			}
			awc["items"].append(awc_item)
			awc_is_dirty = True
		else:
			quotation_item_to_remove.append(item)

	# step 4
	# remove invalid quotation items
	for item in quotation_item_to_remove:
		idx = quotation.items.index(item)
		del quotation.items[idx]
		quotation_is_dirty = True

	if quotation_is_dirty:
		apply_cart_settings(quotation=quotation)
		quotation.flags.ignore_permissions = True
		quotation.save()
		frappe.db.commit()

	if awc_is_dirty:
		set_awc_session(awc)

	collect_totals(quotation, awc)

@frappe.whitelist(allow_guest=True, xss_safe=True)
def cart(data=None, action=None):
	if data and isinstance(data, basestring):
		data = json.loads(data)

	customer = get_current_customer()
	quotation = None
	if customer:
		cart_info = get_cart_quotation()
		quotation = cart_info.get('doc')

	awc = get_awc_session()

	if not awc:
		awc = clear_awc_session()

	if quotation:
		sync_awc_and_quotation(awc, quotation)

	if not action:
		return { "data": awc, "success": True}

	elif action == "addToCart":

		# need basic data validation here
		if not data.get("sku"):
			return { "success": False, "message": "Invalid Data" }

		if not data.get("qty"):
			return { "success": False, "message": "Invalid Data" }

		if quotation:
			product = get_product_by_sku(data.get("sku")).get("data")

			item = quotation.append("items", {
				"doctype": "Quotation Item",
				"item_code": data.get("sku"),
				"qty": data.get("qty"),
				"warehouse": product.get("warehouse")
			})

			apply_cart_settings(quotation=quotation)
			quotation.flags.ignore_permissions = True
			quotation.save()
			frappe.db.commit()

			collect_totals(quotation, awc)
			data["id"] = item.name

		awc["items"].append(data)
		set_awc_session(awc)

		return { "success": True, "data": data, "totals": awc.get("totals") }

	elif action == "removeFromCart":
		index = find_index(awc["items"], lambda item: item.get("id")==data.get("id") )
		if index > -1:
			del awc["items"][index]
			set_awc_session(awc)

			if quotation:
				quotation.set("items", quotation.get("items", {"name": ["!=", data.get("id")]}))
				apply_cart_settings(quotation=quotation)
				quotation.flags.ignore_permissions = True
				quotation.save()
				frappe.db.commit()

				collect_totals(quotation, awc)


			return { "success": True, "totals": awc.get("totals") }

		return { "success": False, "message": "Item not found."}

	else:
		return { "success": False, "message": "Unknown Command." }

@frappe.whitelist()
def create_transaction(gateway_service, billing_address, shipping_address):

	if isinstance(billing_address, basestring):
		billing_address = json.loads(billing_address)

	if isinstance(shipping_address, basestring):
		shipping_address = json.loads(shipping_address)

	result = {
		"success": False,
		"error": "Unknown Internal Error"
	}

	# fetch customer
	customer = get_current_customer()
	# fetch quotation
	cart_info = get_cart_quotation()
	quotation = cart_info.get('doc')
	# fetch awc
	awc = get_awc_session()
	# make sure quotation and awc match
	sync_awc_and_quotation(awc, quotation)
	# create awc transaction to process payments first
	# sales order and friends will be generated from this data
	data = {
		"doctype": "AWC Transaction",
		"title": "Web Order",
		"description": "Online Web Order",
		"status": "Initiated",
		"payer_name": quotation.contact_person,
		"payer_email": quotation.contact_email,
		"amount": quotation.grand_total,
		"currency": quotation.currency,
		"session": json.dumps(awc),
		"order_id": quotation.name,
		"gateway_service": gateway_service
	}

	print(billing_address)
	print(shipping_address)
	data.update(billing_address)
	data.update(shipping_address)

	transaction = frappe.get_doc(data)

	transaction.flags.ignore_permissions = 1
	transaction.save()
	frappe.db.commit()

	# fetch only payment request info
	result["data"] = { key: transaction.get(key) for key in \
					('amount', 'currency', 'order_id', 'title', \
					 'description', 'payer_email', 'payer_name')}

	result["data"]["reference_doctype"] = "AWC Transaction"
	result["data"]["reference_docname"] = transaction.name
	result["success"] = True
	del result["error"]

	return result
