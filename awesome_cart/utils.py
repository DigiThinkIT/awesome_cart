# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import os

import frappe
import traceback

from frappe import _
from frappe.utils import random_string

from .dbug import pretty_json


def update_context(context):

    path = frappe.local.request.path[1:]
    print("Path: %s" % frappe.local.request.path)
    context.current_date = ''


def on_session_creation(login_manager):
    pass


def on_logout(login_manager):
    # destroys cart session on logout
    sid = frappe.local.session.get(
        "awc_sid", frappe.local.request.cookies.get("awc_sid"))
    if sid:
        awc_sid = "awc_session_{0}".format(sid)
        frappe.cache().set_value(awc_sid, None)

@frappe.whitelist()
def get_order_data():
    sales_orders = frappe.get_all("Sales Order", filters={
        "owner": frappe.session.user}, limit_page_length=1, order_by="creation DESC")
    if sales_orders:
        order_doc = frappe.get_doc("Sales Order", sales_orders[0].get("name"))

        items_data = []
        for item in order_doc.items:
            items_data.append(
                [{
                    'sku': item.item_code,
                    'name': item.item_name,
                    'price': item.rate,
                    'quantity': item.qty
                }])

        transaction_data = {
            'transactionId': order_doc.name,
            'transactionTotal': order_doc.grand_total,
            'transactionShipping': order_doc.total_taxes_and_charges,
            'transactionProducts': items_data
        }

        return transaction_data
