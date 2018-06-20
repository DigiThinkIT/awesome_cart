window.awc_checkout = {};

//valiadation for shipping addr form fields
jQuery.fn.extend({
	disable: function(state) {
		return this.each(function() {
			this.disabled = state;
		});
	}
});

awc_checkout = {

	showPage: function(page) {

		if (awc_checkout._page_change_id) {
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
					.removeClass('active')
					.trigger('page_hide');
				$bc.addClass('active');
				$bc.trigger('page_show');
			}
		}).bind(awc_checkout, page), 100);

	},

	coupon_reject:function(err) {
		frappe.msgprint(err.message);
	},

	validate: function() {
		var checkout_enabled = true;

		var totals = cart.totals;

		$('#checkout-confirm-totals .other-totals').empty();
		// find shipping total
		$.each(totals.other, function(i, t) {
			$('#checkout-confirm-totals .other-totals').append($(
				'<div class="other"><span class="method">' + t.label + ':</span><span class="value">' + cart.storeAdapter.formatCurrency(t.value) + '</span></div>'
			));
		});

		$('#checkout-confirm-totals .sub-total .value').text(cart.storeAdapter.formatCurrency(totals.sub_total));
		$('#checkout-confirm-totals .grand-total .value').text(cart.storeAdapter.formatCurrency(totals.grand_total));

		if (awc_checkout.shipping_provider) {
			var shipping_validation_response = awc_checkout.shipping_provider.validate();
			var shipping_summary = awc_checkout.shipping_provider.getSummary();
			$('#checkout-confirm-shipping .content').empty().append(shipping_summary);

			if (shipping_validation_response.valid == false) {
				checkout_enabled = false
			}

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

	nextPage: function() {
		var $page = $('.panel:visible');
		awc_checkout.showPage($page.next());
		$('html, body').animate({ scrollTop: $('#awc-forms').offset().top - 60 }, 'slow');
	},

	build_shipping_widget: function($shipping_container, addresses, shipform) {
		awc_utils.build_address_widget($shipping_container, {
			addresses: addresses,
			label: "Shipping Address",
			data_type: "ship",

			on_init: function($widget) {
				var $container = $widget.find('.awc-addresses-container');
				var $pickup_option = $(frappe.render_template("awc_pickup_option"));

				$container.prepend($pickup_option);

				$pickup_option.click(function() {
					$("#checkout-shipping-method").hide();
					$("#bc-shipping-method").hide();

					$shipping_container.find('.addr').not($(this).find('.addr')).removeClass('awc-selected');
					$(this).find('.addr').addClass("awc-selected");

					awc_checkout.shipping_provider.reset_method();
					awc_checkout.shipping_provider.set_method("PICK UP").then(function(r) {
						awc_checkout.onCartChanges();
						awc_checkout.showPage("#checkout-billing");
						return r;
					})
				});

			},

			on_address_click: function($addr) {
				var country = $($addr).find("span#country.line")[0].innerText;
				awc_checkout.setAffirmDisplay(country);
				if ( awc_checkout.shipping_provider.data.ship_method == "PICK UP") {
					awc_checkout.shipping_provider.reset_method();
				}
				$("#checkout-shipping-method").show();
				$("#bc-shipping-method").show();
				awc_checkout.showPage('#checkout-shipping-method');
				$('html, body').animate({ scrollTop: $('#awc-forms').offset().top - 60 }, 'slow');
			},

			on_delete_click: function($addr, e) {
				frappe.call({
					method: "awesome_cart.utils.delete_address",
					args: { "address_name": $addr.closest('div').attr('data-name') }
				});
				$addr.closest('.address-item').remove();
				$shipping_container.find(".awc-addresses-container div.addr[data-name=" + $(this).closest("div").attr("data-name") + "]").parent().remove();
			},

			on_edit_click: function($addr, e) {
				$("#awc-shipping-form .awc-form").trigger("reset");
				$('#awc-shipping-form.awc-form')
					.attr('data-name', $addr.attr('data-name'));

				$('#awc_ship__title').val($addr.find('span#title').text());
				$('#awc_ship__contact').val($addr.find('span#contact').text());
				$('#awc_ship__phone').val($addr.find('span#phone').text());
				$('#awc_ship__line1').val($addr.find('span#line1').text());
				$('#awc_ship__line2').val($addr.find('span#line2').text());
				$('#awc_ship__city').val($addr.find('span#city').text());
				$('#awc_ship__state').val($addr.find('span#state').text());
				$('#awc_ship__zip').val($addr.find('span#postal_code').text());
				$('#awc_ship__country').val($addr.find('span#country').text());
				$('#awc_ship__is_residential').val($addr.attr('data-is-residential'));

				$addr.addClass('edited');
				$('#awc-shipping-form .btn-nextbtn').text('Save');
				$('#checkout-shipping .field.required input').change();
				$('#checkout-shipping .field.required select').change();

				awc_checkout.showPage('#checkout-shipping');
				$('html, body').animate({
					scrollTop: $('#awc-forms').offset().top - 60
				}, 'slow');
			}
		});
	},

	build_billing_widget: function($billing_container, addresses, billform, default_address) {
		awc_utils.build_address_widget($billing_container, {
			addresses: addresses,
			label: "Billing Address",
			data_type: "bill",
			default_address: default_address,

			on_address_click: function($addr) {
				awc_checkout.showPage('#checkout-confirmation');
				$('html, body').animate({
					scrollTop: $('#awc-forms').offset().top - 60
				}, 'slow');
			},

			on_delete_click: function($addr, e) {
				frappe.call({
					method: "awesome_cart.utils.delete_address",
					args: { "address_name": $addr.closest('div').attr('data-name') }
				});
				$addr.closest('.address-item').remove();
				$billing_container.find(".awc-addresses-container div.addr[data-name=" + $(this).closest("div").attr("data-name") + "]").parent().remove();
			},

			on_edit_click: function($addr, e) {

				// lets figure out if this address is being used on shipping
				// if so, we'll need to insert this edit instead of saving to
				// avoid changing the shipping address and shipping method.
				// so, we'll invoke the new address form instead prefilled with
				// this address values.
				if (awc_checkout.shipping_provider.data && $addr.attr("data-name") == awc_checkout.shipping_provider.data.shipping_address) {
					awc_checkout.displayAddNewBillingAddress({
						title: $addr.find('span#title').text(),
						phone: $addr.find('span#phone').text(),
						line1: $addr.find('span#line1').text(),
						line2: $addr.find('span#line2').text(),
						city: $addr.find('span#city').text(),
						state: $addr.find('span#state').text(),
						pincode: $addr.find('span#pincode').text(),
						country: $addr.find('span#country').text()
					});
					return;
				}

				$("#gateway-selector-billing-form").trigger("reset")
				$('#gateway-selector-billing-form.awc-form')
					.attr('data-name', $addr.attr('data-name'));

				$('#billing_title').val($addr.find('span#title').text());
				$('#billing_phone').val($addr.find('span#phone').text());
				$('#billing_line1').val($addr.find('span#line1').text());
				$('#billing_line2').val($addr.find('span#line2').text());
				$('#billing_city').val($addr.find('span#city').text());
				$('#billing_state').val($addr.find('span#state').text());
				$('#billing_pincode').val($addr.find('span#postal_code').text());
				$('#billing_country').val($addr.find('span#country').text());

				$addr.addClass('edited');

				$('#form-bill-addr .btn-nextbtn').text('Save');
				$('#form-bill-addr .field.required input').change();
				$('#form-bill-addr .field.required select').change();
				$('#select-bill-addr').css('display', 'none');
				$('#form-bill-addr').css('display', 'block');
			}
		});

		awc_checkout.setup_billing_new_form($billing_container, addresses, billform);

	},

	setup_billing_new_form: function($billing_container, addresses, billform) {

		$('#form-bill-addr .btn-nextbtn').click(function() {
			if ($('#form-bill-addr .btn-nextbtn').text() == 'Next') {
				$('#ship-form-err-msg').remove();
				if (billform.title == true && billform.phone == true && billform.address_1 == true && billform.city == true && billform.country == true) {
					var address = {
						address_title: $('#billing_title').val(),
						address_phone: $('#billing_phone').val(),
						address_line1: $('#billing_line1').val(),
						address_line2: $('#billing_line2').val(),
						address_city: $('#billing_city').val(),
						address_state: $('#billing_state').val(),
						address_country: $('#billing_country').val(),
						address_zip: $('#billing_pincode').val()
					};

					frappe.call({
						method: "awesome_cart.utils.new_address",
						args: { address: address },
						freeze: 1,
						callback: function(r) {
							console.log("NEW ADDRESS: ", r);

							if ( r.address_name ) {
								addresses.unshift(r.message);

								$('#select-bill-addr').show();
								$('#form-bill-addr').hide();
								$('#form-bill-addr').attr('data-select', 'false');
								$('#select-bill-addr .addr').removeClass('awc-selected');

								$('#billing_title').val('');
								$('#billing_phone').val('');
								$('#billing_line1').val('');
								$('#billing_line2').val('');
								$('#billing_city').val('');
								$('#billing_state').val('');
								$('#billing_country').val('');
								$('#billing_pincode').val('');

								awc_checkout.build_billing_widget($billing_container, addresses, billform, r.message.name);

								//awc_checkout.showPage('#checkout-confirmation');
								$('html, body').animate({ scrollTop: $('#awc-forms').offset().top - 60 }, 'slow');
							}
						}
					});

				} else {
					$(this).parent().prepend("<p id='ship-form-err-msg' style='color:red;'>Please fill in the required fields</p>");
				}
			} else if ($('#form-bill-addr .btn-nextbtn').text() == 'Save') {
				if (billform.title == true && billform.phone == true && billform.address_1 == true && billform.city == true && billform.country == true) {
					var address = {
						address_name: $('#gateway-selector-billing-form.awc-form').attr('data-name'),
						address_title: $('#billing_title').val(),
						address_phone: $('#billing_phone').val(),
						address_line1: $('#billing_line1').val(),
						address_line2: $('#billing_line2').val(),
						address_city: $('#billing_city').val(),
						address_state: $('#billing_state').val(),
						address_country: $('#billing_country').val(),
						address_zip: $('#billing_pincode').val()
					};
					$('#awc-billing-addrs .edited span#phone').text($('#billing_phone').val());
					$('#awc-billing-addrs .edited span#line1').text($('#billing_line1').val());
					$('#awc-billing-addrs .edited span#line2').text($('#billing_line2').val());
					$('#awc-billing-addrs .edited span#city').text($('#billing_city').val());
					$('#awc-billing-addrs .edited span#state').text($('#billing_state').val());
					$('#awc-billing-addrs .edited span#postal_code').text($('#billing_pincode').val());
					$('#awc-billing-addrs .edited span#country').text($('#billing_country').val());
					$('#awc-billing-addrs .addr .edited').removeClass('edited');
					$('#form-bill-addr .btn-nextbtn').text('Next');
					frappe.call({
						method: "awesome_cart.utils.edit_address",
						args: { address: address }
					});
					$('#select-bill-addr').css('display', 'block');
					$('#form-bill-addr').css('display', 'none');
					$('#form-bill-addr.awc-form').removeAttr('data-name');
				} else {
					$('#ship-form-err-msg').remove();
					$(this).parent().prepend("<p id='ship-form-err-msg' style='color:red;'>Please fill in the required fields</p>");
				}
			}
		});

		// add new billing address button
		$billing_container.find(".btn-primary").click(function(e) {
			awc_checkout.displayAddNewBillingAddress();
		});

		// billing form back button click
		$("#form-bill-addr .btn-back").click(function(e) {
			e.preventDefault();
			$('#form-bill-addr').attr('data-select', 'false');
			$('#select-bill-addr .addr').removeClass('awc-selected');
			$('#select-bill-addr').css('display', 'block');
			$('#form-bill-addr').css('display', 'none');
		});

	},

	/**
	 * Displays the "Add new billing address" form
	 * @arg data - An address is object formart to preset before displaying the form.
	 */
	displayAddNewBillingAddress: function(data) {
		$('#checkout-billing .addr').removeClass('awc-selected');
		$('#form-bill-addr').attr('data-select', 'true');
		$("#gateway-selector-billing-form.awc-form").trigger("reset");
		if ( data ) {
			for(var key in data) {
				var value = data[key];
				if ( typeof(value) != 'function' ) {
					$('#billing_' + key).val(value);
				}
			}
		}
		$('#gateway-selector-billing-form.awc-form .field.required input').change();
		$('#gateway-selector-billing-form.awc-form .field.required select').change();
		$('#select-bill-addr').css('display', 'none');
		$('#form-bill-addr').css('display', 'block');
	},

	setupPage: function() {
		awc_utils.get_user_addresses(function(err, addresses) {
			if ( err ) {
				// TODO: Show user some kind of error if we can't get addresses
				console.error(err);
			} else {
				var $shipping_container = $("#awc-shipping-addrs");
				var $billing_container = $("#awc-billing-addrs");

				var shipform = {
					"title": false,
					"phone": false,
					"address_1": false,
					"city": false,
					"country": false,
				};

				//validation for billing address form fields
				var billform = {
					"title": false,
					"phone": false,
					"address_1": false,
					"city": false,
					"country": false,
				};

				// setup shipping address //////////////////////////////////////////
				// awc_utils code at js/awc_utils.js
				awc_checkout.build_shipping_widget($shipping_container, addresses, shipform);

				// setup billing address ///////////////////////////////////////////
				awc_checkout.build_billing_widget($billing_container, addresses, billform);

				$('.panel .btn-next').click(awc_checkout.nextPage); //click for all next btn on all pages

				$('#checkout-shipping-address .btn-next')
					.click(function(e) {
						awc_checkout.showPage('#checkout-shipping-method')
						$('html, body').animate({ scrollTop: $('#awc-forms').offset().top - 60 }, 'slow');
					})

				$("#use-customer-fedex-acc > label > input[type='checkbox']").click(function (){
					if($("#use-customer-fedex-acc > label > input[type='checkbox']").data("toggle")) {
						$("#use-customer-fedex-acc > label > input[type='checkbox']").data("toggle", false);
						awc_checkout.validate();
						$("#awc-shipping-method > li > label > input[type='radio'][checked='checked']").trigger('change')
					} else if(!$("#use-customer-fedex-acc > label > input[type='checkbox']").data("toggle")){
						$("#use-customer-fedex-acc > label > input[type='checkbox']").data("toggle", true);
						awc_checkout.validate();
						$("#awc-shipping-method > li > label > input[type='radio'][checked='checked']").trigger('change')
					}
				})
				// map address "edit" Button clicks ----------------------------

				$('#checkout-confirm-shipping .btn-primary')
					.click(function(e) {
						if ($('#checkout-shipping').attr('data-select') == "true") {
							e.preventDefault();
							awc_checkout.showPage('#checkout-shipping');
							$('html, body').animate({ scrollTop: $('#awc-forms').offset().top - 60 }, 'slow');
						} else {
							e.preventDefault();
							awc_checkout.showPage('#checkout-shipping-address');
							$('html, body').animate({ scrollTop: $('#awc-forms').offset().top - 60 }, 'slow');
						}
					})


				$('#checkout-confirm-billing .btn-primary')
					.click(function(e) {
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

				// checkout error back button
				$('#checkout-error .btn-primary')
					.click(function() {
						awc_checkout.showPage('#checkout-billing');
						$('html, body').animate({ scrollTop: $('#awc-forms').offset().top - 60 }, 'slow');
					})

				// checkout accept terms
				$('#checkout-confirmation input[name="accept_terms"]')
					.change(function() {
						awc_checkout.validate();
					})

				// map breadcrumb clicks ---------------------------------------
				$('#bc-shipping').click(function(e) {
					if ($('#checkout-shipping').attr('data-select') == "true") {
						e.preventDefault();
						awc_checkout.showPage('#checkout-shipping');
					} else {
						e.preventDefault();
						awc_checkout.showPage('#checkout-shipping-address');
					}
				});

				$('#bc-billing').click(function(e) {
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

				$('#bc-checkout').click(function(e) {
					e.preventDefault();
					awc_checkout.showPage('#checkout-confirmation');
				});

				$('#bc-shipping-method').click(function(e) {
					e.preventDefault();
					awc_checkout.showPage('#checkout-shipping-method');
				});

				// add new shipping address button
				$shipping_container.find(".btn-primary").click(function(e) {
					$('#checkout-shipping-address .addr').removeClass('awc-selected');
					$('#checkout-shipping').attr('data-select', 'true');
					$("#awc-shipping-form .awc-form").trigger("reset");
					$('#checkout-shipping .field.required input').change();
					$('#checkout-shipping .field.required select').change();
					awc_checkout.showPage('#checkout-shipping');
					$('html, body').animate({ scrollTop: $('#awc-forms').offset().top - 60 }, 'slow');
				});

			}

			// shipping form back button click
			$("#awc-shipping-form .btn-back").click(function(e) {
				e.preventDefault();
				$('#checkout-shipping').attr('data-select', 'false');
				$('#checkout-shipping-address .addr').removeClass('awc-selected');
				awc_checkout.showPage('#checkout-shipping-address');
				$('html, body').animate({ scrollTop: $('#awc-forms').offset().top - 60 }, 'slow');
			});

			// handles change event and key up event properly plus auto complete support from browser
			$('input[id^=awc_ship__], select[id^=awc_ship__], input[id^=billing_], select[id^=billing_]')
			.bind('keyup change', function() {
				// determine field name by the last word in the id attribute
				var field_name = $(this).attr('data-type')
				// determine if we are handling a select element
				var is_select = $(this).is('select');
				// get element value differently if a select element vs an input
				var value = is_select ? $(this).find(':selected').attr('value') : $(this).val();
				// determine if we are handling a shipping field or billing field
				var is_ship = $(this).attr('id').indexOf('ship') >= 0;
				// get a reference to the shipform or billform depending on what is_ship value
				var data = is_ship ? shipform : billform;
				data[field_name] = value ? true : false;
			});

			$('#awc-shipping-form .btn-nextbtn').click(function() {
				if ($('#awc-shipping-form .btn-nextbtn').text() == 'Next') {
					if (shipform.title == true && shipform.phone == true && shipform.address_1 == true && shipform.city == true && shipform.country == true) {
						//adding newly entered shipping address on billing address tab in awc
						var div = document.createElement('div');
						div.setAttribute('class', 'col-md-12 col-sm-12 address-item');
						var line2str, statestr, zipstr;
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
						if ($('#awc_ship__zip').val()) {
							zipstr = "<span id='postal_code'>" + $('#awc_ship__zip').val() + "</span>.<br>";
						} else {
							zipstr = "<br>";
						}
						str = ['<div class="well">',
								'<div id="same-as-ship-addr" class="addr">',
									'<div class="address">',
										'<span class="glyphicon glyphicon-tag"></span>',
										'<span id="title">' + $('#awc_ship__title').val() + '</span>',
										'<br>',
										'<span class="glyphicon glyphicon-user"></span>',
										'<span id="contact">' + $('#awc_ship__contact').val() + '</span>',
										'<br>',
										'<span class="glyphicon glyphicon-map-marker pull-left"></span>',
										'<div style="padding-left: 1.5em;">',
											'<span id="line1" class="line">' + $('#awc_ship__contact').val() + ' </span>',
											line2str,
											'<span id="city">' + $('#awc_ship__city').val() + '</span>,',
											statestr,
											zipstr,
											'<span id="country" class="line">' + $('#awc_ship__country').val() + '</span>',
											'<br></div>',
										'<span class="glyphicon glyphicon-phone-alt"></span>',
										'<span id="phone">' + $('#awc_ship__phone').val() + '</span>',
										'<br> </div>',
									'</div>',
								'</div>'].join("")

						div.innerHTML = str;

						$('#awc-billing-addrs #same-as-ship-addr.addr').parent().remove();

						$('#awc-billing-addrs div.row .awc-addresses-container').prepend(div);
						$('#awc-billing-addrs #same-as-ship-addr.addr').click(function(e) {
							e.stopPropagation();
							$('#awc-billing-addrs .awc-selected').removeClass('awc-selected');
							$(this).addClass('awc-selected');
							awc_checkout.showPage('#checkout-confirmation');
							$('html, body').animate({ scrollTop: $('#awc-forms').offset().top - 60 }, 'slow');
						})

						awc_checkout.showPage('#checkout-shipping-method');
						$('#ship-form-err-msg').remove();

						awc_checkout.setAffirmDisplay($('#awc_ship__country').val());

					} else {
						$('#ship-form-err-msg').remove();
						$(this).parent().prepend("<p id='ship-form-err-msg' style='color:red;'>Please fill in the required fields</p>");
					}
				} else if ($('#awc-shipping-form .btn-nextbtn').text() == 'Save') {
					if (shipform.title == true && shipform.phone == true && shipform.address_1 == true && shipform.city == true && shipform.country == true) {
							var address = {
							address_name: $('#awc-shipping-form.awc-form').attr('data-name'),
							address_title: $('#awc_ship__title').val(),
							address_is_residential: $('#awc_ship__is_residential').val(),
							address_phone: $('#awc_ship__phone').val(),
							address_contact: $('#awc_ship__contact').val(),
							address_line1: $('#awc_ship__line1').val(),
							address_line2: $('#awc_ship__line2').val(),
							address_city: $('#awc_ship__city').val(),
							address_state: $('#awc_ship__state').val(),
							address_zip: $('#awc_ship__zip').val(),
							address_country: $('#awc_ship__country').val()
						};
						$('#awc-shipping-addrs .edited span#title').text($('#awc_ship__title').val());
						$('#awc-shipping-addrs .edited span#phone').text($('#awc_ship__phone').val());
						$('#awc-shipping-addrs .edited span#contact').text($('#awc_ship__contact').val());
						$('#awc-shipping-addrs .edited span#line1').text($('#awc_ship__line1').val());
						$('#awc-shipping-addrs .edited span#line2').text($('#awc_ship__line2').val());
						$('#awc-shipping-addrs .edited span#city').text($('#awc_ship__city').val());
						$('#awc-shipping-addrs .edited span#state').text($('#awc_ship__state').val());
						$('#awc-shipping-addrs .edited span#postal_code').text($('#awc_ship__zip').val());
						$('#awc-shipping-addrs .edited span#country').text($('#awc_ship__country').val());
						$('#awc-shipping-addrs .addr.edited').attr('data-is-residential', $('#awc_ship__is_residential').val());
						$('#awc-shipping-addrs .addr.edited').removeClass('edited');
						$('#awc-shipping-form .btn-nextbtn').text('Next');

						awc_checkout.setAffirmDisplay($('#awc_ship__country').val());

						frappe.call({
							method: "awesome_cart.utils.edit_address",
							args: { address: address }
						});
						awc_checkout.showPage('#checkout-shipping-address');
						$('html, body').animate({ scrollTop: $('#awc-forms').offset().top - 60 }, 'slow');
						$('#awc-shipping-form.awc-form').removeAttr('data-name');
					} else {
						$('#ship-form-err-msg').remove();
						$(this).parent().prepend("<p id='ship-form-err-msg' style='color:red;'>Please fill in the required fields</p>");
					}
				}

			});

		}); // eof-fetch user addresses

		// create a full cart feed from awesom cart js
		cart.newCartFeed('cart-full', {
			container: '#cart-full',
			tpl: cart.template('cart-full')
		})

		function onCartChanges() {
			var totals = cart.totals;

			$('#checkout-confirm-totals .sub-total .value').text(cart.storeAdapter.formatCurrency(totals.sub_total));
			$('#checkout-confirm-totals .grand-total .value').text(cart.storeAdapter.formatCurrency(totals.grand_total));
			if ( totals.discount_total ) {
				$('#checkout-confifm-discount .discount-total .value').text(cart.storeAdapter.formatCurrency(totals.discount_total))
			}

			// FIX: Babelfish issue, cart.totalItems getter not invoked in IF statement
			var totalItems = cart.totalItems;
			// make sure panels are visible once cart is processed and has items
			if (totalItems > 0) {
				$('#checkout-panels').fadeIn('fast')
			} else {
				$('#checkout-panels').hide()
			}
		}

		awc_checkout.onCartChanges = onCartChanges;

		cart.on('init', onCartChanges);
		cart.on('update', onCartChanges);
		cart.on("tpl-ready", function() {
			$("#disabled-coupon-apply:not(.awc-bound)").addClass("awc-bound").click(function() {
				frappe.msgprint("Please Log In or Signup to use Coupon Codes");
			});
		});

	},
	setAffirmDisplay: function(country) {
		if (country != "United States") {
			$("#gateway-selector-options div.field.custom:has('input[value=\"affirm\"]')").hide();
			$("#gateway-selector-options div.field.custom:has('input[value=\"authorizenet\"]')").click();
		} else {
			$("#gateway-selector-options div.field.custom:has('input[value=\"affirm\"]')").show();
		}
	}
}

$(function() {
	awc_checkout.setupPage();
});
