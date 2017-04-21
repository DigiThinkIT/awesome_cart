awc.ErpnextAdapter = function() {
  awc.StoreAdapter.prototype.constructor.call(this)
  this._templates = {}
}

awc.ErpnextAdapter.prototype = Object.create(awc.StoreAdapter.prototype)
/* TODO: fetch actual default currency from ERPNEXT */
awc.ErpnextAdapter.prototype.getCurrency = function() { return "USD"; }
/* TODO: fetch actual currecy symbol from ERPNext */
awc.ErpnextAdapter.prototype.getCurrencySymbol = function() { return "$"; }
/* TODO: fetch currecy formatting from ERPNext */
awc.ErpnextAdapter.prototype.formatCurrency = function(currency, decimals) { return this.getCurrencySymbol() + currency.toFixed(decimals?decimals:2); }

awc.ErpnextAdapter.prototype.init = function() {
  var base = this;
  this.itemCache = {};
  return new awc.Promise(function(resolve, reject) {
    resolve(base.fetchCartSession())
  })
}

awc.ErpnextAdapter.prototype.loadTemplate = function(name) {
  // simple template caching.  Always cache the promise
  if ( this._templates[name] === undefined ) {
    return this._templates[name] = awc.get('/awc_template/' + name).then(function(resp) {
      return resp.body
    });
  } else {
    return this._templates[name]
  }
}

awc.ErpnextAdapter.prototype.fetchCartSession = function() {
  var base = this;
  return awc.get('/api/method/awesome_cart.awc.cart')
    .then(function(resp, xhr) {
      var data = JSON.parse(resp.body).message;
      if ( data.data.totals ) {
        base._totals = data.data.totals;
      }
      return data;
    })
}

awc.ErpnextAdapter.prototype.sessionAction = function(action, data) {
  var base = this;
  return new awc.Promise(function(resolve, reject) {
    frappe.call({
      method: "awesome_cart.awc.cart",
      freeze: 1,
      args: {
        action: action,
        data: data
      },
      callback: function(result) {
        if ( result.message.success ) {
          if ( result.message.totals ) {
            base._totals = result.message.totals;
          }

          resolve(result.message.data)
        } else {
          reject(result.message.data)
        }
      }
    })
  })

}

awc.ErpnextAdapter.prototype.getProductBySKU = function(sku, detailed) {
  var base = this;
  if ( base.itemCache[sku] !== undefined ) {
    // return promise if curretly fetching
    if ( base.itemCache[sku].constructor == awc.Promise ) {
      return base.itemCache[sku];
    } else if (base.itemCache[sku].detailed == detailed) {
      // else return promise with cache data
      return new awc.Promise(function(resolve) {
        resolve(base.itemCache[sku]);
      })
    }
  }

  // otherwise, fetch item from backend
  return base.itemCache[sku] = new awc.Promise(function(resolve, reject) {
    frappe.call({
      method: "awesome_cart.awc.get_product_by_sku",
      args: { sku: sku, detailed: detailed?1:0 },
      freeze: 1,
      callback: function(result) {
        if ( result.message.success ) {
          // only cache detailed items
          if ( detailed ) {
            base.itemCache[sku] = { data: message.data, detailed: detailed };
          }

          resolve(result.message.data)
        } else {
          reject(result.message)
        }
      }
    })
  })

}

awc.ErpnextAdapter.prototype.fetchProducts = function(tags, terms, start, limit) {
  if ( !tags ) tags = []
  var base = this;
  return new awc.Promise(function(resolve, reject) {
    frappe.call({
      method: "awesome_cart.awc.fetch_products",
      args: { tags: tags.join(','), terms: terms, start: start?start:0, limit: limit },
      freeze: 1,
      callback: function(result) {
        console.log("Fetch products");
        console.log(result);
        if ( result.message.success ) {
          if ( result.message.data.totals ) {
            base._totals = result.message.data.totals;
          }

          resolve(result.message.data)
        } else {
          reject(result.message.data)
        }
      }
    })
  })
}

awc.ErpnextAdapter.prototype.validate = function(gateway_request, gateway_service) {
  /* We expect this method to be called when awc's gateway provider's submit
     button is clicked.

     We'll use this call to feed payment request information to the gateway
     before it can be submitted */

    if ( !gateway_request ) {
      throw "gateway_request is not set";
    }

    frappe.call({
      method: "awesome_cart.awc.create_transaction",
      args: {
        gateway_service: gateway_service,
        billing_address: awc_checkout.billing_address,
        shipping_address: awc_checkout.shipping_address
      },
      freeze: true,
      freeze_message: "Validating Order",
      callback: function(data) {
        var result = data.message;
        if ( result.success ) {
          // copy validation data to continue checkout process
          for(var k in result.data ) {
            gateway_request[k] = result.data[k];
          }

          console.log("Preparing for checkout!", gateway_request);
          awc_checkout.gateway_provider.process(gateway_request, function(err, data) {
            if ( err ) {
              console.error(err);
            } else {
              window.location.href = data.redirect_to;
            }
          });
        } else {
          console.error(data);
        }
      },
      error: function(err) {
        console.error(err)
      }
    })
}

var AwcShippingProvider = Class.extend({
	init: function(cart) {
		this._last_values = "";
		this._packages = [];
		this._cart = cart;
		this._cart.on("update", this._on_cart_update);
		this._on_cart_update()
		this.valid = false;
		this.method_valid = false;

	},
	_on_cart_update: function() {
		var base = this;
		this._packages = [];
		this._cart.fetchCartItems()
			.then(function(items) {
				base._last_values = "#invalid";
			});
	},
	form: function(data) {
		this.data = data;
	},
	validate: function() {
		var base = this;
		var $form = $('#awc-shipping-form');
		var $method_form = $('#awc-shipping-method');

		this.data.address_1 = $form.find('input[name="address_1"]').val();
		this.data.address_2 = $form.find('input[name="address_2"]').val();
		this.data.city = $form.find('input[name="city"]').val();
		this.data.state = $form.find('input[name="state"]').val();
		this.data.pincode = $form.find('input[name="pincode"]').val();
		this.data.country = $form.find('select[name="country"] option:checked').attr('value');

		var result = {
			valid: true,
			address: this.data
		}

		if ( !this.data.address_1 ) {
			result.valid = false;
		}
		if ( !this.data.city ) {
			result.valid = false;
		}
		if ( !this.data.state ) {
			result.valid = false;
		}
		if ( !this.data.pincode ) {
			result.valid = false;
		}
		if ( !this.data.country ) {
			result.valid = false;
		}
		if ( !this.data.ship_method ) {
			result.method_valid = false;
		}

		this.valid = result.valid;
		if ( result.valid ) {
			$("#bc-shipping").addClass("valid");

			// build values hash to avoid sending
			var last_values = this.data.address_1 +
				this.data.address_2 + this.data.city +
				this.data.state + this.data.pincode +
				this.data.country;

			if ( last_values != this._last_values ) {
				this._last_values = last_values;
				$method_form.empty();

				frappe.call({
					method: "awesome_cart.awc.get_shipping_rate",
					args: {
						address: this.data,
					},
					callback: function(response) {
						var result = response.message;
						if ( result && result.constructor == Array && result.length > 0 ) {
							base._shipping_methods = result;

							$.each(result, function(i, method) {
								var checked="";
								var is_default = false;
								if ( base.data.ship_method && base.data.ship_method == method.name ) {
									is_default = true;		// auto select last ship method selection if available
								} else if ( !base.data.ship_method ) {
									is_default = i == 0;	// select first item by default
								}

								if ( is_default ) {
									checked="checked='checked'";
									base.data.ship_method = method.name;
									base.method_valid = true;
									$("#bc-shipping-method").addClass("valid");
								}
								var $method = $(
									'<li>'+
										'<label>'+
											'<input type="radio" name="awc_shipping_method" value="' + method.name + '"' + checked + '>' +
											'<span class="label">' + method.label + " + $" + method.fee + '</span>' +
										'</label>' +
									'</li>');
								$method_form.append($method);
								$method.find('input').change(function() {
									if ( $(this).is(":checked") ) {
										base.data.ship_method = $(this).val();
										base.method_valid = true;
										console.log("Ship Method", base.data.ship_method);
										// force cart ui validation so ui updates with new data on click
										awc_checkout.validate();
									}
								})
							});

							if ( !base.data.ship_method ) {
								// if there was nothing selected by default, go back and select
								// first item. This can occur if address method was removed due
								// to a change of address from a previous selection
								$method_form.find('index[type="radio"]:first').click();

							}

							// finally trigger validation once more to update ui with default selections
							awc_checkout.validate();
						} else {
							base.method_valid = false;
							$("#bc-shipping-method").removeClass("valid");
							$method_form.empty();
							$method_form.append('<li class="error">Invalid Shipping Address. Edit your shipping information to get shipping quote.</li>');
						}
					}
				})
			}
		} else {
			$("#bc-shipping").removeClass("valid");
			$method_form.empty();
			$method_form.append('<li class="error">Invalid Shipping Address. Edit your shipping information to get shipping quote.</li>');
		}

		// only validate if both address and shipping method validated
		result.valid = result.valid && base.method_valid

		return result;
	},
	getSummary: function() {
		var base = this;
		// NOTE: lazy way of setting up address dom.
		// consider moving to templates(will require checking script load order)
		var ln=function(name, nl) {
			if ( nl === undefined ) {
				nl = true;
			}

			var txt = "";
			if ( name in base.data && base.data[name] ) {
				txt = base.data[name];
				if ( nl ) {
					txt += "<br>";
				}
			}

			return txt;
		}

		if ( this.valid ) {
			// find shipping method label data
			var ship_method = "";
			for(var i in this._shipping_methods) {
				var method = this._shipping_methods[i];
				console.log(method.name, base.data.ship_method);
				if ( base.data.ship_method == method.name ) {
					ship_method = '<div class="row"><div class="col-sm-6 shipping_method label">Shipping method</div>' +
						'<div class="col-sm-6 shipping_method value">' + method.label + ' + $' + method.fee + '</div>' +
						'</div>';
					break;
				}
			}

			console.log("Ship method? ", ship_method);
			return '<div class="row">' +
				'<address class="col-sm-12">' +
					ln("address_1") +
					ln("address_2") +
					ln("city", 0) + ", " + ln("state", 0) + " " + ln("pincode") +
					ln("country") +
				'</address>' +
			'</div>'+
			ship_method;
		} else {
			return '<p class="error">Shipping address incomplete. Please go back and review.</p>';
		}

	}
})

// Initialize awc cart
var cart = new awc.AwesomeCart({
  storeAdapter: new awc.ErpnextAdapter()
});

cart.on("after-add-to-cart", function(items) {
  console.log("Products added", items);
});

awc.debug.level = 5;

$(function() { cart.bootstrap() });
