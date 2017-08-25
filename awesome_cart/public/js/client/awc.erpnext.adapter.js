awc.debug.level = awc.debug.LEVEL.NONE;

awc.Errors.CallException = awc.Errors.customError("CallException", function (
	message, errors, parse_error, status, recoverable, xhr, textStatus) {
	this.message = message;
	this.errors = errors;
	this.parse_error = parse_error;
	this.status = status;
	this.recoverable = recoverable;
	this.xhr = xhr;
	this.textStatus = textStatus;
});

/* soft wrapper over frappe.call to improve error handling */
awc.call = function (method, args, freeze, freeze_message) {
	var last_error = null;
	var call_log = method + (args ? "(" + JSON.stringify(args) + ")" : "()");

	var opts = {
		method: method,
		args: args,
		freeze: freeze,
		freeze_message: freeze_message
	}

	// opts = {"method": "PYTHON MODULE STRING", "args": {}, "callback": function(r) {}}
	frappe.prepare_call(opts);
	if (opts.freeze) {
		frappe.freeze();
	}

	return new awc.Promise(function (resolve, reject) {

		var deferred = $.ajax({
			type: opts.type || "POST",
			url: "/",
			data: opts.args,
			dataType: "json",
			headers: {
				"X-Frappe-CSRF-Token": frappe.csrf_token
			},
			statusCode: opts.statusCode || {
				404: function (xhr) {
					frappe.msgprint(__("Not found"));
				},
				403: function (xhr) {
					frappe.msgprint(__("Not permitted"));
				},
				200: function (data, xhr) {
					if (opts.callback)
						opts.callback(data);
					if (opts.success)
						opts.success(data);
				}
			}
		}).always(function (data) {
			if (opts.freeze) {
				frappe.unfreeze();
			}

			// executed before statusCode functions
			if (data.responseText) {
				try {
					data = JSON.parse(data.responseText);
				} catch (ex) {
					data = {
						__server_messages: [{
							message: data.responseText
						}]
					};
				}
			}
			frappe.process_response(opts, data);
		});

		deferred.then(function (data, textStatus, xhr) {
			awc.debug.log(call_log, data, textStatus, xhr);
			var parse_error = false;
			if (typeof data === "string") {
				try {
					data = JSON.parse(data);
				} catch (ex) {
					parse_error = ex;
					console.error(ex);
				}
			}
			var status = xhr.statusCode().status;

			resolve({
				data: data,
				parse_error: parse_error,
				status: status,
				recoverable: data.recoverable || false,
				xhr: xhr,
				textStatus: textStatus
			});
		}, function (xhr, textStatus) {
			awc.debug.error(call_log, xhr, textStatus);
			var status = xhr.statusCode().status;
			var _server_messages = null;
			var parse_error = false;
			var errors = [];

			if (xhr.responseJSON && xhr.responseJSON._server_messages) {
				try {
					_server_messages = JSON.parse(xhr.responseJSON._server_messages);
				} catch (ex) {
					_server_messages = xhr.responseJSON._server_messages;
					parse_error = ex;
					errors.push(ex);
				}
			}

			if (_server_messages && _server_messages.contructor == Array) {
				try {
					for (var i = 0; i < _server_messages.length; i++) {
						var msg;
						try {
							msg = JSON.parse(_server_messages[i]);
							if (msg.message) {
								msg = msg.message;
							}
						} catch (ex) {
							msg = ex
						}
						errors.push("Server Error: " + msg);
					}
				} catch (ex) {
					errors.push(data._server_messages);
					errors.push(ex);
				}
			} else if (_server_messages && _server_messages.exc) {
				errors.push(_server_messages.exc);
			}

			reject(new awc.Errors.CallException(
				"Error during a backend call. Please check your Internet connection",
				errors, parse_error, status, false, xhr, textStatus
			));

		});

		return null;
	});
}

awc.ErpnextAdapter = function () {
	awc.StoreAdapter.prototype.constructor.call(this)
	this._templates = {}
	this.products = new awc.DataStore([], this._fetchProducts.bind(this))
}

awc.ErpnextAdapter.prototype = Object.create(awc.StoreAdapter.prototype)
/* TODO: fetch actual default currency from ERPNEXT */
awc.ErpnextAdapter.prototype.getCurrency = function () {
	return "USD";
}
/* TODO: fetch actual currecy symbol from ERPNext */
awc.ErpnextAdapter.prototype.getCurrencySymbol = function () {
	return "$";
}
/* TODO: fetch currecy formatting from ERPNext */
awc.ErpnextAdapter.prototype.formatCurrency = function (currency, decimals) {
	return this.getCurrencySymbol() + currency.toFixed(decimals ? decimals : 2);
}

awc.ErpnextAdapter.prototype.init = function () {
	var base = this;
	this.itemCache = {};
	return base.fetchCartSession()
}

awc.ErpnextAdapter.prototype._fetchProducts = function (filter, start, limit) {
	var tags = []
	var terms = null

	// accept an array as tags list
	// or an object with tags field
	if (filter.contructor === Array) {
		tags = filter;
	} else if (typeof filter == "object") {
		tags = filter.tags || []
		terms = filter.terms;
	} else {
		tags = filter
	}

	var base = this;

	return new awc.Promise(function (resolve, reject) {
		awc.call("awesome_cart.awc.fetch_products", {
				tags: tags.join(','),
				terms: terms,
				start: start ? start : 0,
				limit: limit
			}, 1)
			.then(function (resp) {
				var result = resp.data;

				if (result.message.success) {
					if (result.message.data.totals) {
						base._totals = result.message.data.totals;
					}

					resolve(result.message.data)
				} else {
					reject(result.message.data)
				}
				return resp;
			}).catch(function (err) {
				reject(err);
			});

		return null;
	});
}

awc.ErpnextAdapter.prototype.loadTemplate = function (name) {
	// simple template caching.  Always cache the promise
	if (this._templates[name] === undefined) {
		return this._templates[name] = awc.get('/awc_template/' + name).then(function (resp) {
			return resp.body
		});
	} else {
		return this._templates[name]
	}
}

awc.ErpnextAdapter.prototype.fetchCartSession = function () {
	var base = this;
	return awc.get('/api/method/awesome_cart.awc.cart')
		.then(function (resp, xhr) {
			var data = JSON.parse(resp.body).message;
			if (data.data.totals) {
				base._totals = data.data.totals;
			}
			return data;
		})
}

awc.ErpnextAdapter.prototype.sessionAction = function (action, data) {
	var base = this;
	return new awc.Promise(function (resolve, reject) {
		awc.call("awesome_cart.awc.cart", {
				action: action,
				data: data
			}, 1)
			.then(function (resp) {
				var result = resp.data;

				dispalyAddr(result.message.shipping_address_name);
				if (result.message.success) {
					if (result.message.totals) {
						base._totals = result.message.totals;
					}
					resolve(result.message)
				} else {
					reject(result.message.data)
				}

				return resp;
			}).catch(function (err) {
				awc.debug.error("Error during session action");
				awc.debug.error(err);
				reject(err);
			})

		return null;
	});

}

function dispalyAddr(shipaddr) {
	$('#same-as-ship-addr').attr('data-name', shipaddr);
	$('#awc-shipping-form').attr('data-name', shipaddr);
}

awc.ErpnextAdapter.prototype.getProductBySKU = function (sku, detailed) {
	var base = this;
	var skuHash = detailed + ":" + sku;
	if (base.itemCache[skuHash] !== undefined) {
		// return promise if curretly fetching
		if (base.itemCache[skuHash].constructor == awc.Promise) {
			return base.itemCache[skuHash];
		} else {
			// else return promise with cache data
			return new awc.Promise(function (resolve) {
				return resolve(base.itemCache[skuHash]);
			});
		}
	}

	// otherwise, fetch item from backend
	return base.itemCache[skuHash] = new awc.Promise(function (resolve, reject) {
		awc.call("awesome_cart.awc.get_product_by_sku", {
				sku: sku,
				detailed: detailed ? 1 : 0
			}, 1)
			.then(function (resp) {
				var result = resp.data;
				if (result.message.success) {
					resolve(base.itemCache[skuHash] = result.message.data)
				} else {
					reject(result.message)
				}

				return resp;
			})
			.catch(function (err) {
				awc.debug.error("Error while fething product by sku");
				awc.debug.error(err)
				reject(err);
			});

		return null;
	});

}

awc.ErpnextAdapter.prototype.fetchProducts = function (tags, terms, start, limit) {
	return this.products.query({
		tags: tags,
		terms: terms
	}, start, limit)
}

awc.ErpnextAdapter.prototype.validate = function (gateway_request, gateway_service) {
	/* We expect this method to be called when awc's gateway provider's submit
	   button is clicked.

	   We'll use this call to feed payment request information to the gateway
	   before it can be submitted */

	if (!gateway_request) {
		throw "gateway_request is not set";
	}

	awc_checkout.showPage('#checkout-processing')
	awc.call("awesome_cart.awc.create_transaction", {
			gateway_service: gateway_service,
			billing_address: awc_checkout.billing_address,
			shipping_address: awc_checkout.shipping_address,
			instructions: $("#order-instructions").val()
		}, 1, "Validating Order")
		.then(function (resp) {
			var result = resp.data.message;
			if (result.success) {
				// copy validation data to continue checkout process
				for (var k in result.data) {
					gateway_request[k] = result.data[k];
				}

				awc.debug.log("Preparing for checkout!", gateway_request);
				awc_checkout.gateway_provider.process(gateway_request, function (err, data) {
					console.log(data)
					if (err) {
						if ((!err.errors || err.errors.length == 0) || err.status == 500) {
							$('#checkout-error .msg').text("There was an internal server error while processing your order. Please contact us or try again later");
						} else {
							$('#checkout-error .msg').text(err.errors.join(', '));
						}

						awc.debug.error(err);
						awc_checkout.showPage('#checkout-error');
					} else {
						awc.call("awesome_cart.utils.get_order_data", null, 1)
							.then(function (resp) {
								var result = resp.data;
								window.dataLayer = window.dataLayer || []
								dataLayer.push(result.message)
								awc_checkout.showPage('#checkout-success');
								window.location.href = data.redirect_to;
								return resp;
							})
							.catch(function (err) {
								var result = resp.errors;
								awc.debug.error(err);
								awc_checkout.showPage('#checkout-success');
								window.location.href = data.redirect_to;
							})

					}
				});
			} else {
				$('#checkout-error .msg').text(result.error);
				awc.debug.error(result.error);
				awc_checkout.showPage('#checkout-error');
			}

			return resp;
		})
		.catch(function (err) {
			awc.debug.error("Error while sending gateway data");
			awc.debug.error(err);
			if ((!err.errors || err.errors.length == 0) || err.status == 500) {
				$('#checkout-error .msg').text("There was an internal server error while processing your order. Please contact us or try again later");
			} else {
				$('#checkout-error .msg').text(err.errors.join(", "));
			}
			awc_checkout.showPage('#checkout-error');
		})
}

var AwcShippingProvider = Class.extend({
	init: function (cart) {
		this._last_values = "";
		this._packages = [];
		this._cart = cart;
		this._cart.on("update", this._on_cart_update.bind(this));
		this._on_cart_update()
		this.valid = false;
		this.method_valid = false;
		this.fee = 0;
		this.label = "";
		this.data = {};

		var $form = $('#awc-shipping-form');
		var on_update = function () {
			var field = {
				name: $(this).attr('data-type'),
				value: $(this).val()
			};
			$form.trigger('field-change', field);
		}

		$form.find('input[name="address_1"]').change(on_update);
		$form.find('input[name="address_2"]').change(on_update);
		$form.find('input[name="city"]').change(on_update);
		$form.find('input[name="state"]').change(on_update);
		$form.find('input[name="pincode"]').change(on_update);
		$form.find('select[name="country"]').change(on_update);

		cart.on("shipping_rates", this.update_shipping_rates.bind(this));
	},
	_on_cart_update: function () {
		var base = this;
		this._packages = [];
		this._cart.fetchCartItems()
			.then(function (items) {
				//base._last_values = "#invalid";
			});
	},
	form: function (data) {
		this.data = data || {};
	},

	calculate_shipping: function (method, address) {
		var base = this;
		var $form = $('#awc-shipping-form');
		var $method_form = $('#awc-shipping-method');
		return cart.calculateShipping(method, address)
			.catch(awc.Errors.CallException, function (err) {
				awc.debug.error(err);


				$("#bc-shipping").removeClass("valid");
				$method_form.fadeOut('fast');
				$method_form.parent().find('.error .error-invalid-address').hide();
				$method_form.parent().find('.error .error-other').text(err.message);
				$method_form.parent().find('.error .error-other').show();
				$method_form.parent().find('.error').fadeIn('fast');
				$method_form.parent().find('.spinner').fadeOut('fast');
			});
	},

	update_shipping_rates: function (rates) {
		var base = this;
		var $form = $('#awc-shipping-form');
		var $method_form = $('#awc-shipping-method');
		var update = true;
		if (base._shipping_methods) {
			if (awc._.isEqual(base._shipping_methods, rates)) {
				$method_form.fadeIn('fast');
				$method_form.parent().find('.error').fadeOut('fast');
				$method_form.parent().find('.spinner').fadeOut('fast');
				return;
			}
		}
		base._shipping_methods = rates;
		$method_form.empty();

		if (rates.length > 0) {
			var last_selected_method = base.data.ship_method;
			base.data.ship_method = null;

			$.each(rates, function (i, method) {
				var checked = "";
				var is_default = false;
				if (last_selected_method && last_selected_method == method.name) {
					is_default = true; // auto select last ship method selection if available
					base.data.ship_method = method.name;
				} else if (!last_selected_method) {
					is_default = i == 0; // select first item by default
					if (is_default) {
						base.data.ship_method = method.name;
					}
				}

				if (is_default) {
					checked = "checked='checked'";
					base.data.ship_method = method.name;
					base.method_valid = true;
					base.fee = method.fee;
					base.label = method.label;
					$("#bc-shipping-method").addClass("valid");
				}
				var $method = $(
					'<li>' +
					'<label>' +
					'<input type="radio" name="awc_shipping_method" value="' + method.name + '"' + checked + '>' +
					'<span class="label">' + method.label + " + $" + method.fee.toFixed(2) + '</span>' +
					'</label>' +
					'</li>');
				$method_form.append($method);
				$method.find('input').data('method', method);
				$method.find('input').change(function () {
					if ($(this).is(":checked")) {
						var method = $(this).data('method');
						base.method_valid = true;
						base.data.ship_method = method.name;
						base.fee = method.fee;
						base.label = method.label;
						base.calculate_shipping(base.data.ship_method);
						base.validate();
					}
				})
			});

			if (!$method_form.find('input[type="radio"]').is(':checked')) {
				// if there was nothing selected by default, go back and select
				// first item. This can occur if address method was removed due
				// to a change of address from a previous selection
				$method_form.find('input[type="radio"]:first').click();
			}

			$method_form.fadeIn('fast');
			$method_form.parent().find('.error').fadeOut('fast');
			$method_form.parent().find('.spinner').fadeOut('fast');

			// finally trigger validation once more to update ui with default selections
			awc_checkout.validate();
		} else {
			base.method_valid = false;
			$("#bc-shipping-method").removeClass("valid");
			$method_form.fadeOut('fast');
			$method_form.parent().find('.error .error-invalid-address').show();
			$method_form.parent().find('.error .error-other').empty();
			$method_form.parent().find('.error .error-other').hide();
			$method_form.parent().find('.error').fadeIn('fast');
			$method_form.parent().find('.spinner').fadeOut('fast');
		}
	},

	validate: function () {

		var base = this;
		var $form = $('#awc-shipping-form');
		var $method_form = $('#awc-shipping-method');
		var address_data = {};

		if ($("#checkout-shipping").attr('data-select') == 'true') {
			address_data.shipping_address = $('#awc-shipping-form').attr('data-name');
			address_data.phone = $form.find('input[name="phone"]').val();
			address_data.address_1 = $form.find('input[name="address_1"]').val();
			address_data.address_2 = $form.find('input[name="address_2"]').val();
			address_data.city = $form.find('input[name="city"]').val();
			address_data.state = $form.find('input[name="state"]').val();
			address_data.pincode = $form.find('input[name="pincode"]').val();
			address_data.country = $form.find('select[name="country"] option:checked').attr('value');
			address_data.is_residential = $form.find('select[name="is_residential"] option:checked').attr('value') == 1 ? 1 : 0;
			address_data.address_type = "Shipping";
		} else {
			address_data.shipping_address = $('#shipping-addrs div.selected').attr('data-name');
			address_data.phone = $('#shipping-addrs .selected span#phone').text();
			address_data.address_1 = $('#shipping-addrs .selected span#line1').text();
			address_data.address_2 = $('#shipping-addrs .selected span#line2').text();
			address_data.city = $('#shipping-addrs .selected span#city').text();
			address_data.state = $('#shipping-addrs .selected span#state').text();
			address_data.pincode = $('#shipping-addrs .selected span#postal_code').text();
			address_data.country = $('#shipping-addrs .selected span#country').text();
			address_data.is_residential = $('#shipping-addrs div.selected').attr('data-is-residential');
			address_data.address_type = $('#shipping-addrs div.selected').attr('data-address-type');
		}

		current_address_data = {
			shipping_address: this.data.shipping_address,
			phone: this.data.phone,
			address_1: this.data.address_1,
			address_2: this.data.address_2,
			city: this.data.city,
			state: this.data.state,
			pincode: this.data.pincode,
			country: this.data.country,
			address_type: this.data.address_type,
			is_residential: this.data.is_residential
		}

		if (awc._.isEqual(current_address_data, address_data) && this.result) {
			$form.trigger('address_change', this.data);
			this.result.valid = this.address_valid && base.method_valid
			return this.result;
		}

		$.each(address_data, function (k, v) {
			base.data[k] = v;
		});

		$form.trigger('address_change', this.data);

		var result = {
			valid: true,
			address: this.data
		}

		if (!this.data.address_1) {
			result.valid = false;
		}
		if (!this.data.city) {
			result.valid = false;
		}
		if (!this.data.pincode) {
			result.valid = false;
		}
		if (!this.data.country) {
			result.valid = false;
		}
		if (!this.data.phone) {
			result.valid = false;
		}

		var update_shipping_method = false;
		if (!this.data.ship_method) {
			result.method_valid = false;
			base.fee = 0;
			base.label = "";
		}

		this.valid = result.valid;
		if (result.valid) {
			$("#bc-shipping").addClass("valid");
			$method_form.fadeOut('fast');
			$method_form.parent().find('.error').fadeOut('fast');
			$method_form.parent().find('.spinner').fadeIn('fast');
			base.calculate_shipping(this.data.ship_method, this.data);
		} else {
			$("#bc-shipping").removeClass("valid");
			$method_form.fadeOut('fast');
			$method_form.parent().find('.error .error-invalid-address').show();
			$method_form.parent().find('.error .error-other').empty();
			$method_form.parent().find('.error .error-other').hide();
			$method_form.parent().find('.error').fadeIn('fast');
			$method_form.parent().find('.spinner').fadeOut('fast');
		}

		// only validate if both address and shipping method validated
		this.address_valid = result.valid;
		result.valid = result.valid && base.method_valid
		this.result = result;

		return result;
	},
	getSummary: function () {
		var base = this;
		// NOTE: lazy way of setting up address dom.
		// consider moving to templates(will require checking script load order)
		var ln = function (name, nl) {
			if (nl === undefined) {
				nl = true;
			}

			var txt = "";
			if (name in base.data && base.data[name]) {
				txt = base.data[name];
				if (nl) {
					txt += "<br>";
				}
			}

			return txt;
		}

		if (this.result.valid) {
			// find shipping method label data
			var ship_method = "";
			for (var i in this._shipping_methods) {
				var method = this._shipping_methods[i];
				if (base.data.ship_method == method.name) {
					ship_method = '<div class="row"><div class="col-sm-6 shipping_method label">Shipping method</div>' +
						'<div class="col-sm-6 shipping_method value">' + method.label + ' + $' + method.fee + '</div>' +
						'</div>';
					break;
				}
			}

			return '<div class="row">' +
				'<address class="col-sm-12">' +
				ln("address_1") +
				ln("address_2") +
				ln("city", 0) + ", " + ln("state", 0) + " " + ln("pincode") +
				ln("country") +
				'</address>' +
				'</div>';
			/*+
				  ship_method;*/
		} else {
			return '<p class="error">Shipping address incomplete. Please go back and review.</p>';
		}

	}
})

// Initialize awc cart
var cart = new awc.AwesomeCart({
	storeAdapter: new awc.ErpnextAdapter()
});

cart.scan_forms = function () {

	function toTitleCase(str) {
		if (str) {
			return str.replace(/\b\w+/g, function (txt) {
				return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
			});
		}

		return str;
	}

	// handle smart placeholder labels
	$('.awc-form .field').not('.awc-form-bound').each(function () {
		var $field = $(this);
		var $input = $(this).find('input:first, select:first, textarea:first');
		$field.addClass(".awc-form-bound");

		var validate_phone = function (value) {
			// simple validation for phone numbers, just remove all non numeric values
			return value.replace(/[^\d\(\)\+\-\s]/g, '');
		}

		var validate_value = function (value, $field) {
			if (value) {
				$field.addClass('hasvalue');
			} else {
				$field.removeClass('hasvalue');
			}
		}

		$input
			.change(function () {
				var is_select = $(this).is('select');
				if ($(this).is('[data-auto-titlecase]')) {
					$(this).val(toTitleCase($(this).val()))
				}
				if ($(this).is('[data-validate-phone]')) {
					$(this).val(validate_phone($(this).val()));
				}
				var value = is_select ? $(this).find(':selected').attr('value') : $(this).val();
				validate_value(value, $field);
			})
			.keyup(function () {
				validate_value($(this).val(), $field);
			})
			.blur(function () {
				$field.removeClass('focus');
				if ($(this).is('[data-auto-titlecase]')) {
					$(this).val(toTitleCase($(this).val()))
				}
				if ($(this).is('[data-validate-phone]')) {
					$(this).val(validate_phone($(this).val()));
				}
			})
			.focus(function () {
				$field.addClass('focus');
			});

		// allow priming classes with defaults
		$input.change();
	});
}

cart.on('tpl-ready', function () {
	cart.scan_forms();
})


$(function () {
	var $popup = $('<div id="add-to-cart-popup"><h2>Product Added to Cart</h2><a class="btn btn-default btn-cancel">Continue Shopping</a><a href="/cart" class="btn btn-default btn-success">Checkout</a></div>');
	$('body').append($popup);
	$popup.hide();
	$popup.find('.btn-cancel').click(function () {
		$popup.fadeOut('fast');
	})

	awc.call("awesome_cart.power.get_power_user_settings")
		.then(function (resp) {
			var data = resp.data;
			if (data.message == "Power User") {
				var cwindow_tpl = cart.template("Power User - Customer Select Window").promiseReady();
				var $cwindow = null;

				if (data.selected_customer) {
					window.selected_customer = data.selected_customer;
					var $customer = $('<div class="customer-name"><span class="for">For:</span> ' + data.selected_customer + '</div>');
					$("#website-post-login a.dropdown-toggle:first").append($customer);
					$("#website-post-login a.dropdown-toggle .full-name").addClass('is-power-user');
					if (data.selected_customer_image) {
						var $logo = $('<img />');
						$logo.attr('src', data.selected_customer_image);
						$("#website-post-login a.dropdown-toggle .avatar").empty().append($logo);
					}
				}

				if (data.customers && data.customers.length > 1) {
					cwindow_tpl = cwindow_tpl.then(function (tpl) {
						$cwindow = $(tpl.beginRender({
							customers: data.customers
						}));
						$('body').append($cwindow);
						$cwindow.hide();
						tpl.endRender();

						$cwindow.find('.item').click(function () {
							var customer_name = $(this).attr("data-customer-name");

							awc.call("awesome_cart.power.set_cart_customer", {
									customer_name: customer_name
								}, 1)
								.then(function (resp) {
									window.location.reload();
									return resp;
								})
								.catch(function (err) {
									awc.debug.error(err);
								});
						});

						var $menu_item = $('<li data-label="Switch Customer"><a rel="nofollow">Switch Customer</a></li>');
						$("#website-post-login ul.dropdown-menu").append($menu_item);
						$menu_item.find('a').click(function () {
							$cwindow.fadeIn('fast');
						});

						return tpl;
					});

				}
				// if not selected a customer yet and we have more than one customer
				if (!data.selected_customer && data.customers && data.customers.length > 1) {
					cwindow_tpl.then(function (tpl) {
						$cwindow.fadeIn('fast');
						return tpl;
					});
				}
			}

			return resp;
		})
		.catch(function (err) {
			// ignore backend error as we don't want to break users navigation
			// on this check.
			awc.debug.error(err);
		});

	cart.on('add-to-cart-completed', function () {
		$popup.fadeIn('fast');
	})
	cart.bootstrap()
});