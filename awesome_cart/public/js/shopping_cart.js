// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt
// shopping cart
frappe.provide("shopping_cart");

// seting up a wrapper on original update_cart method so we can inject
// our changes
var update_cart_bak = shopping_cart.update_cart.bind(shopping_cart);

$.extend(shopping_cart, {
	update_cart: function(opts) {
		// original cart won't allow "Guest" user to add 
		// items to cart, so we change it temporarily
		// and update_cart code stays intact

		var tmp_fullname = full_name;
		full_name = "Guest User";		try {
			return update_cart_bak(opts);
		} finally {
			// then we set it back
			full_name = tmp_fullname;
		}
	},
	/*
	set_cart_count: function() {
		var cart_count = getCookie("cart_count");
		
		if($(".cart-icon").length == 0) {
			$('<div class="cart-icon">\
				<a href="/cart" class="text-muted small">\
					<div class="btn btn-primary cart"> Cart\
						<span id="cart-count" class="label">\
						</span>\
					</div>\
				</a></div>').appendTo($('.mobile-menu'))
		}
		
		var $cart = $('.cart-icon');
		var $badge = $cart.find("#cart-count");

		if(parseInt(cart_count) === 0 || cart_count === undefined) {
			$cart.css("display", "none");
		}
		else {
			$cart.css("display", "inline");
		}

		if(cart_count) {
			$badge.html(cart_count);
		} else {
			$badge.remove();
		}
	}*/
});
