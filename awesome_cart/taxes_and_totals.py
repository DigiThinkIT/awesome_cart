from __future__ import unicode_literals

import json

from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals
from .session import *
from .awesome_cart.doctype.awc_coupon.awc_coupon import calculate_coupon_discount

class AWCCalculateTaxesAndTotals(calculate_taxes_and_totals):
    """Extends the default implementation of calculate_taxes_and_totals controller
    to include our own calculation over existing ones"""

    def __init__(self, doc):
        super(AWCCalculateTaxesAndTotals, self).__init__(doc)

    def set_discount_amount(self):
        """extends set_discount_amount method to add coupon calculations first"""
        if self.doc.meta.get_field("coupon_code"):
            self.calculate_coupon_discounts()
        super(AWCCalculateTaxesAndTotals, self).set_discount_amount()

    def calculate_coupon_discounts(self):
        if self.doc.docstatus > 0:
            return # avoid messing with doc if already submitted

        awc_session = get_awc_session()

        # Apply coupon codes
        if self.doc.coupon_code:
            shipping_method = awc_session.get("shipping_method", {}).get("name") or (self.doc.get("fedex_shipping_method") or "").upper()
            discount, msg, apply_discount_on, coupon_state, has_services, has_total_limit = calculate_coupon_discount({
                "items": self.doc.items,
                "code": self.doc.coupon_code,
                "accounts": self.doc.get("taxes", []),
                "grand_total": self.doc.base_grand_total,
                "net_total": self.doc.base_net_total,
                "is_ground_shipping": True if "GROUND" in shipping_method else False
            })

            # appends our discount data list, we can use it to list discount details
            # for our cart templates or even on print formats if need be
            if self.doc.meta.get_field("discount_data"):
                self.doc.discount_data = json.dumps(coupon_state)

            if not has_total_limit and discount is not False and discount != self.doc.discount_amount:
                self.doc.discount_amount = discount
                self.doc.apply_discount_on = apply_discount_on or "Net Total"
            elif discount is False:
                raise msg
        else:
            if self.doc.meta.get_field("discount_data"):
                self.doc.discount_data = None
