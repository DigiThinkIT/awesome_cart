awc.debug.level = awc.debug.LEVEL.NONE;

awc.ErpnextAdapter = function() {
    awc.StoreAdapter.prototype.constructor.call(this)
    this._templates = {}
    this.products = new awc.DataStore([], this._fetchProducts.bind(this))
}

awc.ErpnextAdapter.prototype = Object.create(awc.StoreAdapter.prototype)
    /* TODO: fetch actual default currency from ERPNEXT */
awc.ErpnextAdapter.prototype.getCurrency = function() {
        return "USD";
    }
    /* TODO: fetch actual currecy symbol from ERPNext */
awc.ErpnextAdapter.prototype.getCurrencySymbol = function() {
        return "$";
    }
    /* TODO: fetch currecy formatting from ERPNext */
awc.ErpnextAdapter.prototype.formatCurrency = function(currency, decimals) {
    return this.getCurrencySymbol() + currency.toFixed(decimals ? decimals : 2);
}

awc.ErpnextAdapter.prototype.init = function() {
    var base = this;
    this.itemCache = {};
    return base.fetchCartSession()
}

awc.ErpnextAdapter.prototype._fetchProducts = function(filter, start, limit) {
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

    return new awc.Promise(function(resolve, reject) {
        frappe.call({
            method: "awesome_cart.awc.fetch_products",
            args: {
                tags: tags.join(','),
                terms: terms,
                start: start ? start : 0,
                limit: limit
            },
            freeze: 1,
            callback: function(result) {
                if (result.message.success) {
                    if (result.message.data.totals) {
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

awc.ErpnextAdapter.prototype.loadTemplate = function(name) {
    // simple template caching.  Always cache the promise
    if (this._templates[name] === undefined) {
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
            if (data.data.totals) {
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
                dispalyAddr(result.message.shipping_address_name);
                if (result.message.success) {
                    if (result.message.totals) {
                        base._totals = result.message.totals;
                    }

                    resolve(result.message)
                } else {
                    reject(result.message.data)
                }
            }
        })
    })

}

function dispalyAddr(shipaddr) {
    $('#same-as-ship-addr').attr('data-name', shipaddr);
    $('#awc-shipping-form').attr('data-name', shipaddr);
}

awc.ErpnextAdapter.prototype.getProductBySKU = function(sku, detailed) {
    var base = this;
    var skuHash = detailed + ":" + sku;
    if (base.itemCache[skuHash] !== undefined) {
        // return promise if curretly fetching
        if (base.itemCache[skuHash].constructor == awc.Promise) {
            return base.itemCache[skuHash];
        } else {
            // else return promise with cache data
            return new awc.Promise(function(resolve) {
                return resolve(base.itemCache[skuHash]);
            })
        }
    }

    // otherwise, fetch item from backend
    return base.itemCache[skuHash] = new awc.Promise(function(resolve, reject) {
        frappe.call({
            method: "awesome_cart.awc.get_product_by_sku",
            args: {
                sku: sku,
                detailed: detailed ? 1 : 0
            },
            freeze: 1,
            callback: function(result) {
                if (result.message.success) {
                    resolve(base.itemCache[skuHash] = result.message.data)
                } else {
                    reject(result.message)
                }
            }
        })

        return null;
    })

}

awc.ErpnextAdapter.prototype.fetchProducts = function(tags, terms, start, limit) {
    return this.products.query({
        tags: tags,
        terms: terms
    }, start, limit)
}

awc.ErpnextAdapter.prototype.validate = function(gateway_request, gateway_service) {
    /* We expect this method to be called when awc's gateway provider's submit
       button is clicked.

       We'll use this call to feed payment request information to the gateway
       before it can be submitted */

    if (!gateway_request) {
        throw "gateway_request is not set";
    }

    awc_checkout.showPage('#checkout-processing')
    frappe.call({
        method: "awesome_cart.awc.create_transaction",
        args: {
            gateway_service: gateway_service,
            billing_address: awc_checkout.billing_address,
            shipping_address: awc_checkout.shipping_address,
            instructions: $("#order-instructions").val()
        },
        freeze: true,
        freeze_message: "Validating Order",
        callback: function(data) {
            var result = data.message;
            if (result.success) {
                // copy validation data to continue checkout process
                for (var k in result.data) {
                    gateway_request[k] = result.data[k];
                }

                awc.debug.log("Preparing for checkout!", gateway_request);
                awc_checkout.gateway_provider.process(gateway_request, function(err, data) {
                    if (err) {
                        $('#checkout-error .msg').text(err.error);
                        awc.debug.error(err);
                        awc_checkout.showPage('#checkout-error');
                    } else {
                        frappe.call({
                            method: "awesome_cart.utils.get_order_data",
                            callback: function(result) {
                                window.dataLayer = window.dataLayer || []
                                dataLayer.push(result.message)
                                awc_checkout.showPage('#checkout-success');
                                window.location.href = data.redirect_to;
                            },
                        });

                    }
                });
            } else {
                $('#checkout-error .msg').text(err.error);
                awc.debug.error(result.error);
                awc_checkout.showPage('#checkout-error');
            }
        },
        error: function(err) {
            $('#checkout-error .msg').text(err.error);
            awc.debug.error(err);
            awc_checkout.showPage('#checkout-error');
        }
    })
}

var AwcShippingProvider = Class.extend({
    init: function(cart) {
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
        var on_update = function() {
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
    _on_cart_update: function() {
        var base = this;
        this._packages = [];
        this._cart.fetchCartItems()
            .then(function(items) {
                //base._last_values = "#invalid";
            });
    },
    form: function(data) {
        this.data = data || {};
    },

    update_shipping_rates: function(rates) {
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

            $.each(rates, function(i, method) {
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
                    '<span class="label">' + method.label + " + $" + method.fee + '</span>' +
                    '</label>' +
                    '</li>');
                $method_form.append($method);
                $method.find('input').data('method', method);
                $method.find('input').change(function() {
                    if ($(this).is(":checked")) {
                        var method = $(this).data('method');
                        base.method_valid = true;
                        base.data.ship_method = method.name;
                        base.fee = method.fee;
                        base.label = method.label;
                        cart.calculateShipping(base.data.ship_method);
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
            $method_form.parent().find('.error').fadeIn('fast');
            $method_form.parent().find('.spinner').fadeOut('fast');
        }
    },

    validate: function() {

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

        $.each(address_data, function(k, v) {
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
            cart.calculateShipping(this.data.ship_method, this.data);
        } else {
            $("#bc-shipping").removeClass("valid");
            $method_form.fadeOut('fast');
            $method_form.parent().find('.error').fadeIn('fast');
            $method_form.parent().find('.spinner').fadeOut('fast');
        }

        // only validate if both address and shipping method validated
        this.address_valid = result.valid;
        result.valid = result.valid && base.method_valid
        this.result = result;

        return result;
    },
    getSummary: function() {
        var base = this;
        // NOTE: lazy way of setting up address dom.
        // consider moving to templates(will require checking script load order)
        var ln = function(name, nl) {
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

        if (this.valid) {
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

cart.scan_forms = function() {
    // handle smart placeholder labels
    $('.awc-form .field').not('.awc-form-bound').each(function() {
        var $field = $(this);
        var $input = $(this).find('input:first, select:first, textarea:first');
        $field.addClass(".awc-form-bound");

        $input
            .change(function() {
                var is_select = $(this).is('select');
                var value = is_select ? $(this).find(':selected').attr('value') : $(this).val();

                if (value) {
                    $field.addClass('hasvalue');
                } else {
                    $field.removeClass('hasvalue');
                }
            })
            .keyup(function() {
                if ($(this).val()) {
                    $field.addClass('hasvalue');
                } else {
                    $field.removeClass('hasvalue');
                }
            })
            .blur(function() {
                $field.removeClass('focus');
            })
            .focus(function() {
                $field.addClass('focus');
            });

        // allow priming classes with defaults
        $input.change();
    });
}

cart.on('tpl-ready', function() {
    cart.scan_forms();
})


$(function() {
    var $popup = $('<div id="add-to-cart-popup"><h2>Product Added to Cart</h2><a class="btn btn-default btn-cancel">Continue Shopping</a><a href="/cart" class="btn btn-default btn-success">Checkout</a></div>');
    $('body').append($popup);
    $popup.hide();
    $popup.find('.btn-cancel').click(function() {
        $popup.fadeOut('fast');
    })

    frappe.call({
        method: "awesome_cart.power.get_power_user_settings",
        args: {},
        callback: function(data) {
            if (data.message == "Power User") {
                // if not selected a customer yet and we have more than one customer
                if (!data.selected_customer && data.customers && data.customers.length > 1) {
                    cart.template("Power User - Customer Select Window")
                        .promiseReady()
                        .then(function(tpl) {
                            var $cwindow = $(tpl.beginRender({ customers: data.customers }));
                            $('body').append($cwindow);
                            tpl.endRender();

                            $cwindow.find('.item').click(function() {
                                var customer_name = $(this).attr("data-customer-name");
                                frappe.call({
                                    method: "awesome_cart.power.set_cart_customer",
                                    args: {
                                        customer_name: customer_name
                                    },
                                    freeze: 1,
                                    callback: function() {
                                        window.location.reload();
                                    }
                                });
                            });

                        });
                }
            }
        }
    });



    cart.on('add-to-cart-completed', function() {
        $popup.fadeIn('fast');
    })
    cart.bootstrap()
});
