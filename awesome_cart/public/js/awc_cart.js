window.awc_checkout = {};

awc_checkout = {
	showPage: function (page) {

		if ( awc_checkout._page_change_id ) {
			clearTimeout(awc_checkout._page_change_id);
		}

		awc_checkout._page_change_id = setTimeout((function(page) {
			awc_checkout.validate();
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
		}).bind(awc_checkout, page), 100);

		console.log("Show page: ", page);

	},

	validate: function () {
		var checkout_enabled = true;

		var totals = cart.totals;
		shipping_total = null;

		$('#checkout-confirm-totals .other-totals').empty();
		// find shipping total
		$.each(totals.other, function (i, t) {
			$('#checkout-confirm-totals .other-totals').append($(
				'<div class="other"><span class="method">'+t.label+':</span><span class="value">'+t.value+'</span></div>'
			));

		});

		$('#checkout-confirm-totals .sub-total .value').text(cart.storeAdapter.formatCurrency(totals.sub_total));
		$('#checkout-confirm-totals .grand-total .value').text(cart.storeAdapter.formatCurrency(totals.grand_total));
		
		if (awc_checkout.shipping_provider) {
			var shipping_validation_response = awc_checkout.shipping_provider.validate();
			var shipping_summary = awc_checkout.shipping_provider.getSummary();
			$('#checkout-confirm-shipping .content').empty().append(shipping_summary);

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
				awc_checkout.showPage('#checkout-shipping-method')
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
			awc_checkout.showPage('#checkout-shipping-method');
		})
		//clicking bill addr
		$('#billing-addrs .addr').click(function (e) {
			e.stopPropagation();
			$('#billing-addrs .selected').removeClass('selected');
			$(this).addClass('selected');
			awc_checkout.showPage('#checkout-confirmation');
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
			"phone": false,
			"address_1": false,
			"city": false,
			"pincode": false,
			"country": false,
		};

		//validation for billing address form fields
		var billform = {
			"phone": false,
			"address_1": false,
			"city": false,
			"pincode": false,
			"country": false,
		};

		// handles change event and key up event properly plus auto complete support from browser
		$('input[id^=awc_ship__], select[id^=awc_ship__], input[id^=billing_], select[id^=billing_]')
			.bind('keyup change', function() {
				// determine field name by the last word in the id attribute
				var field_name = $(this).attr('data-type')
				// determine if we are handling a select element
				var is_select = $(this).is('select');
				// get element value differently if a select element vs an input
				var value = is_select?$(this).find(':selected').attr('value'):$(this).val();
				// determine if we are handling a shipping field or billing field
				var is_ship = $(this).attr('id').indexOf('ship') >= 0;
				// get a reference to the shipform or billform depending on what is_ship value
				var data = is_ship?shipform:billform;
				data[field_name] = value?true:false;
			})

		$('#form-bill-addr .btn-nextbtn').click(function () {
			if (billform.phone == true && billform.address_1 == true && billform.city == true && billform.pincode == true && billform.country == true) {
				awc_checkout.showPage('#checkout-confirmation');
				$('#ship-form-err-msg').remove();
			} else {
				$('#ship-form-err-msg').remove();
				$(this).parent().prepend("<p id='ship-form-err-msg' style='color:red;'>Please fill in the required fields</p>");
			}
		})

		$('#awc-shipping-form .btn-nextbtn').click(function () {
			if (shipform.phone == true && shipform.address_1 == true && shipform.city == true && shipform.pincode == true && shipform.country == true) {
				//adding newly entered shipping address on billing address tab in awc
				var div = document.createElement('div');
				div.setAttribute('class', 'col-md-12 col-sm-12');
				div.setAttribute('style', 'padding:0');
				var line2str, statestr;
				if ($('#awc_ship__line2').val()) {
					line2str = "<span id='line2'>" + $('#awc_ship__line2').val() + "</span>,";
				} else {
					line2str = "";
				}
				if ($('#awc_ship__state').val()) {
					statestr = "<span id='stste'>" + $('#awc_ship__state').val() + "</span>,";
				} else {
					statestr = "";
				}
				str = "<div class='well'>\
                			<div id='same-as-ship-addr' class='addr' style='cursor: pointer'>\
                    			<p>\
                        			<span id='line1'>" + $('#awc_ship__line1').val() + "</span>,\
									" + line2str + "\
			                        <span id='city'>" + $('#awc_ship__city').val() + "</span>,\
                        			" + statestr + "\
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
					awc_checkout.showPage('#checkout-confirmation');
				})

				awc_checkout.showPage('#checkout-shipping-method');
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
