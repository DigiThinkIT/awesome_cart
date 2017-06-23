window.awc_checkout = {};

awc_checkout = {
	showPage: function (page) {
		this.validate();

		$('.panel').slideUp('fast');
		$(page).slideDown('fast');
		var bcSelector = $(page).attr('data-bc');
		if (bcSelector) {
			var $bc = $(bcSelector);
			$('#checkout-breadcrumb .breadcrumb')
				.not($bc)
				.removeClass('active');
			$bc.addClass('active');
		}

	},

	validate: function () {
		var checkout_enabled = true;

		if (awc_checkout.shipping_provider) {
			var shipping_validation_response = awc_checkout.shipping_provider.validate();
			var shipping_summary = awc_checkout.shipping_provider.getSummary();
			$('#checkout-confirm-shipping .content').empty().append(shipping_summary);
			var totals = cart.totals;
			shipping_total = null;

			// find shipping total
			$.each(totals.other, function (i, t) {
				if (t.name == "Shipping") {
					shipping_total = t;
				}
			})


			if (shipping_validation_response.valid == false) {
				checkout_enabled = false;
				$('#checkout-confirm-totals .shipping-total .value').empty().append('<span class="error">-</span>');
				$('#checkout-confirm-totals .shipping-total .method').empty().append('<span class="error">(missing)</span>');
			} else {
				if (shipping_total) {
					$('#checkout-confirm-totals .shipping-total .value').empty().text(cart.storeAdapter.formatCurrency(shipping_total.value));
					$('#checkout-confirm-totals .shipping-total .method').empty().text("(" + shipping_total.label + ")");
				}
			}

			$('#checkout-confirm-totals .sub-total .value').text(cart.storeAdapter.formatCurrency(totals.sub_total));
			$('#checkout-confirm-totals .grand-total .value').text(cart.storeAdapter.formatCurrency(totals.grand_total));


			awc_checkout.shipping_address = shipping_validation_response.address;
		}

		if (awc_checkout.gateway_provider) {
			var billing_validation_response = awc_checkout.gateway_provider.validate();
			var billing_summary = awc_checkout.gateway_provider.getSummary();
			$('#checkout-confirm-billing .content').empty().append(billing_summary);

			if (billing_validation_response.valid == false) {
				checkout_enabled = false
			}

			awc_checkout.billing_address = billing_validation_response.address
		}

		// disable checkout until terms and condition box is checked
		if (!$('#confirm-form input[name="accept_terms"]').is(':checked')) {
			checkout_enabled = false;
		}

		awc_checkout.gateway_provider.enable(checkout_enabled);

	},

	nextPage: function () {
		var $page = $('.panel:visible');
		awc_checkout.showPage($page.next());
	},

	setupPage: function () {
		$('.panel .btn-next').click(awc_checkout.nextPage); //click for all next btn on all pages

		$('#checkout-shipping-address .btn-next')
			.click(function (e) {
				awc_checkout.showPage('#checkout-billing')
			})

		// map address "edit" Button clicks ----------------------------

		$('#checkout-confirm-shipping .btn-primary')
			.click(function (e) {
				if ($('#checkout-shipping').attr('data-select') == "true") {
					e.preventDefault();
					awc_checkout.showPage('#checkout-shipping');
				} else {
					e.preventDefault();
					awc_checkout.showPage('#checkout-shipping-address');
				}
			})

		$('#checkout-confirm-billing .btn-primary')
			.click(function (e) {
				if ($('#form-bill-addr').attr('data-select') == 'true') {
					e.preventDefault();
					awc_checkout.showPage('#checkout-billing');
					$('#select-bill-addr').css('display', 'none');
					$('#form-bill-addr').css('display', 'block');
				} else {
					e.preventDefault();
					awc_checkout.showPage('#checkout-billing');
					$('#form-bill-addr').css('display', 'none');
					$('#select-bill-addr').css('display', 'block');
				}
			})

		$('#checkout-error .btn-primary')
			.click(function () {
				awc_checkout.showPage('#checkout-billing');
			})

		$('#checkout-confirmation input[name="accept_terms"]')
			.change(function () {
				awc_checkout.validate();
			})

		// map breadcrumb clicks ---------------------------------------
		$('#bc-shipping').click(function (e) {
			if ($('#checkout-shipping').attr('data-select') == "true") {
				e.preventDefault();
				awc_checkout.showPage('#checkout-shipping');
			} else {
				e.preventDefault();
				awc_checkout.showPage('#checkout-shipping-address');
			}
		});

		$('#bc-billing').click(function (e) {
			if ($('#form-bill-addr').attr('data-select') == 'true') {
				e.preventDefault();
				awc_checkout.showPage('#checkout-billing');
				$('#select-bill-addr').css('display', 'none');
				$('#form-bill-addr').css('display', 'block');
			} else {
				e.preventDefault();
				awc_checkout.showPage('#checkout-billing');
				$('#form-bill-addr').css('display', 'none');
				$('#select-bill-addr').css('display', 'block');
			}
		});

		$('#bc-checkout').click(function (e) {
			e.preventDefault();
			awc_checkout.showPage('#checkout-confirmation');
		});

		$('#bc-shipping-method').click(function (e) {
			e.preventDefault();
			awc_checkout.showPage('#checkout-shipping-method');
		});

		// create a full cart feed from awesom cart js
		cart.newCartFeed('cart-full', {
			container: '#cart-full',
			tpl: cart.template('cart-full')
		})

		function onCartChanges() {
			var totals = cart.totals;

			$('#checkout-confirm-totals .sub-total .value').text(cart.storeAdapter.formatCurrency(totals.sub_total));
			$('#checkout-confirm-totals .grand-total .value').text(cart.storeAdapter.formatCurrency(totals.grand_total));

			// FIX: Babelfish issue, cart.totalItems getter not invoked in IF statement
			var totalItems = cart.totalItems;
			// make sure panels are visible once cart is processed and has items
			if (totalItems > 0) {
				$('#checkout-panels').fadeIn('fast')
			} else {
				$('#checkout-panels').hide()

			}
		}

		$('#checkout-shipping-address .btn-primary').click(function (e) {
			$('#checkout-shipping').attr('data-select', 'true');
			awc_checkout.showPage('#checkout-shipping');
		})

		$('#select-bill-addr .btn-add-bill-addr').click(function (e) {
			$('#form-bill-addr').attr('data-select', 'true');
			$('#select-bill-addr').css('display', 'none');
			$('#form-bill-addr').css('display', 'block');
		})
		//clicking ship addr
		$('#checkout-shipping-address .addr').click(function (e) {
			e.stopPropagation();
			$('#shipping-addrs .selected').removeClass('selected');
			$(this).addClass('selected');
			awc_checkout.showPage('#checkout-billing');
		})
		//clicking bill addr
		$('#billing-addrs .addr').click(function (e) {
			e.stopPropagation();
			$('#billing-addrs .selected').removeClass('selected');
			$(this).addClass('selected');
			awc_checkout.showPage('#checkout-shipping-method');
		})

		$("#awc-shipping-form .btn-back").click(function (e) {
			e.preventDefault();
			$('#checkout-shipping').attr('data-select', 'false');
			$('#checkout-shipping-address .addr').removeClass('selected');
			awc_checkout.showPage('#checkout-shipping-address');
		})

		$("#form-bill-addr .btn-back").click(function (e) {
			e.preventDefault();
			$('#form-bill-addr').attr('data-select', 'false');
			$('#select-bill-addr .addr').removeClass('selected');
			$('#select-bill-addr').css('display', 'block');
			$('#form-bill-addr').css('display', 'none');
		})
		//valiadation for shipping addr form fields
		jQuery.fn.extend({
			disable: function (state) {
				return this.each(function () {
					this.disabled = state;
				});
			}
		});
		var shipform = {
			"title": false,
			"phone": false,
			"line1": false,
			"city": false,
			"state": false,
			"zip": false,
			"country": false,
		};


		$('#awc_ship__title').parent().keyup(function () {
			if ($('#awc_ship__title').val()) {
				$('#awc_ship__title').parent().removeAttr('style');
				shipform.title = true;
			} else {
				$('#awc_ship__title').parent().attr('style', 'border-color: #f00; box-shadow: 0px 0px 5px 1px rgba(255, 0, 0, 0.37);');
				shipform.title = false;
			}
		})
		$('#awc_ship__phone').parent().keyup(function () {
			if ($('#awc_ship__phone').val()) {
				$('#awc_ship__phone').parent().removeAttr('style');
				shipform.phone = true;
			} else {
				$('#awc_ship__phone').parent().attr('style', 'border-color: #f00; box-shadow: 0px 0px 5px 1px rgba(255, 0, 0, 0.37);');
				shipform.phone = false;
			}
		})
		$('#awc_ship__line1').parent().keyup(function () {
			if ($('#awc_ship__line1').val()) {
				$('#awc_ship__line1').parent().removeAttr('style');
				shipform.line1 = true;
			} else {
				$('#awc_ship__line1').parent().attr('style', 'border-color: #f00; box-shadow: 0px 0px 5px 1px rgba(255, 0, 0, 0.37);');
				shipform.line1 = false;
			}
		})
		$('#awc_ship__city').parent().keyup(function () {
			if ($('#awc_ship__city').val()) {
				$('#awc_ship__city').parent().removeAttr('style');
				shipform.city = true;
			} else {
				$('#awc_ship__city').parent().attr('style', 'border-color: #f00; box-shadow: 0px 0px 5px 1px rgba(255, 0, 0, 0.37);');
				shipform.city = false;
			}
		})
		$('#awc_ship__state').parent().keyup(function () {
			if ($('#awc_ship__state').val()) {
				$('#awc_ship__state').parent().removeAttr('style');
				shipform.state = true;
			} else {
				$('#awc_ship__state').parent().attr('style', 'border-color: #f00; box-shadow: 0px 0px 5px 1px rgba(255, 0, 0, 0.37);');
				shipform.state = false;
			}
		})
		$('#awc_ship__zip').parent().keyup(function () {
			if ($('#awc_ship__zip').val()) {
				$('#awc_ship__zip').parent().removeAttr('style');
				shipform.zip = true;
			} else {
				$('#awc_ship__zip').parent().attr('style', 'border-color: #f00; box-shadow: 0px 0px 5px 1px rgba(255, 0, 0, 0.37);');
				shipform.zip = false;
			}
		})
		$('#awc_ship__country').parent().change(function () {
			if ($('#awc_ship__country').val() != "- Select Country -") {
				$('#awc_ship__country').parent().removeAttr('style');
				shipform.country = true;
			} else {
				$('#awc_ship__country').parent().attr('style', 'border-color: #f00; box-shadow: 0px 0px 5px 1px rgba(255, 0, 0, 0.37);');
				shipform.country = false;
			}
		})

		//validation for billing address form fields
		var billform = {
			"title": false,
			"phone": false,
			"line1": false,
			"city": false,
			"state": false,
			"zip": false,
			"country": false,
		};


		$('#billing_title').parent().keyup(function () {
			if ($('#billing_title').val()) {
				$('#billing_title').parent().removeAttr('style');
				billform.title = true;
			} else {
				$('#billing_title').parent().attr('style', 'border-color: #f00; box-shadow: 0px 0px 5px 1px rgba(255, 0, 0, 0.37);');
				billform.title = false;
			}
		})
		$('#billing_phone').parent().keyup(function () {
			if ($('#billing_phone').val()) {
				$('#billing_phone').parent().removeAttr('style');
				billform.phone = true;
			} else {
				$('#billing_phone').parent().attr('style', 'border-color: #f00; box-shadow: 0px 0px 5px 1px rgba(255, 0, 0, 0.37);');
				billform.phone = false;
			}
		})
		$('#billing_line1').parent().keyup(function () {
			if ($('#billing_line1').val()) {
				$('#billing_line1').parent().removeAttr('style');
				billform.line1 = true;
			} else {
				$('#billing_line1').parent().attr('style', 'border-color: #f00; box-shadow: 0px 0px 5px 1px rgba(255, 0, 0, 0.37);');
				billform.line1 = false;
			}
		})
		$('#billing_city').parent().keyup(function () {
			if ($('#billing_city').val()) {
				$('#billing_city').parent().removeAttr('style');
				billform.city = true;
			} else {
				$('#billing_city').parent().attr('style', 'border-color: #f00; box-shadow: 0px 0px 5px 1px rgba(255, 0, 0, 0.37);');
				billform.city = false;
			}
		})
		$('#billing_state').parent().keyup(function () {
			if ($('#billing_state').val()) {
				$('#billing_state').parent().removeAttr('style');
				billform.state = true;
			} else {
				$('#billing_state').parent().attr('style', 'border-color: #f00; box-shadow: 0px 0px 5px 1px rgba(255, 0, 0, 0.37);');
				billform.state = false;
			}
		})
		$('#billing_pincode').parent().keyup(function () {
			if ($('#billing_pincode').val()) {
				$('#billing_pincode').parent().removeAttr('style');
				billform.zip = true;
			} else {
				$('#billing_pincode').parent().attr('style', 'border-color: #f00; box-shadow: 0px 0px 5px 1px rgba(255, 0, 0, 0.37);');
				billform.zip = false;
			}
		})
		$('#billing_country').parent().change(function () {
			if ($('#billing_country').val() != "- Select Country -") {
				$('#billing_country').parent().removeAttr('style');
				billform.country = true;
			} else {
				$('#billing_country').parent().attr('style', 'border-color: #f00; box-shadow: 0px 0px 5px 1px rgba(255, 0, 0, 0.37);');
				billform.country = false;
			}
		})

		$('#form-bill-addr .btn-nextbtn').click(function () {
			if (billform.title == true && billform.phone == true && billform.line1 == true && billform.city == true && billform.state == true && billform.zip == true && billform.country == true) {
				awc_checkout.showPage('#checkout-shipping-method');
				$('#ship-form-err-msg').remove();
			} else {
				$('#ship-form-err-msg').remove();
				$(this).parent().prepend("<p id='ship-form-err-msg' style='color:red;'>Please fill in the required fields</p>");
			}
		})

		$('#awc-shipping-form .btn-nextbtn').click(function () {
			if (shipform.title == true && shipform.phone == true && shipform.line1 == true && shipform.city == true && shipform.state == true && shipform.zip == true && shipform.country == true) {
				//adding newly entered shipping address on billing address tab in awc
				var div = document.createElement('div');
				div.setAttribute('class', 'col-md-12 col-sm-12');
				div.setAttribute('style', 'padding:0');
				var line2str;
				if ($('#awc_ship__line2').val()) {
					line2str = "<span id='line2'>" + $('#awc_ship__line2').val() + "</span>,";
				} else {
					line2str = "";
				}
				str = "<div class='well'>\
                			<div id='same-as-ship-addr' class='addr' style='cursor: pointer'>\
                    			<span id='title'><strong id='title'>" + $('#awc_ship__title').val() + "</strong></strong><br>\
                    			<p>\
                        			<span id='line1'>" + $('#awc_ship__line1').val() + "</span>,\
									" + line2str + "\
			                        <span id='city'>" + $('#awc_ship__city').val() + "</span>,\
                        			<span id='state'>" + $('#awc_ship__state').val() + "</span>,\
		        	                <span id='country'>" + $('#awc_ship__country').val() + "</span>,\
        		    	            <span id='postal_code'>" + $('#awc_ship__zip').val() + "</span>.<br>\
    			                    <span id='phone'>" + $('#awc_ship__phone').val() + "</span>\
                    			</p>\
                			</div>\
            			</div>";
				div.innerHTML = str;
				$('#billing-addrs div.row').prepend(div);
				$('#billing-addrs #same-as-ship-addr.addr').click(function (e) {
					e.stopPropagation();
					$('#billing-addrs .selected').removeClass('selected');
					$(this).addClass('selected');
					awc_checkout.showPage('#checkout-shipping-method');
				})

				awc_checkout.showPage('#checkout-billing');
				$('#ship-form-err-msg').remove();

			} else {
				$('#ship-form-err-msg').remove();
				$(this).parent().prepend("<p id='ship-form-err-msg' style='color:red;'>Please fill in the required fields</p>");
			}
		})




		cart.on('init', onCartChanges);
		cart.on('update', onCartChanges);

	}
}

awc_checkout.setupPage();