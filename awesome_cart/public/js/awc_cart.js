window.awc_checkout = {};

awc_checkout = {
	showPage: function(page) {
		this.validate();

		$('.panel').slideUp('fast');
		$(page).slideDown('fast');
		var bcSelector = $(page).attr('data-bc');
		if ( bcSelector ) {
			var $bc = $(bcSelector);
			$('#checkout-breadcrumb .breadcrumb')
				.not($bc)
				.removeClass('active');
			$bc.addClass('active');
		}

	},

	validate: function() {
		var checkout_enabled = true;

		if ( awc_checkout.shipping_provider ) {
			var shipping_validation_response = awc_checkout.shipping_provider.validate();
			var shipping_summary = awc_checkout.shipping_provider.getSummary();
			$('#checkout-confirm-shipping .content').empty().append(shipping_summary);

			if ( shipping_validation_response.valid == false ) {
				checkout_enabled = false;
			}

			awc_checkout.shipping_address = shipping_validation_response.address;
		}

		if ( awc_checkout.gateway_provider ) {
			var billing_validation_response = awc_checkout.gateway_provider.validate();
			var billing_summary = awc_checkout.gateway_provider.getSummary();
			$('#checkout-confirm-billing .content').empty().append(billing_summary);

			if ( billing_validation_response.valid == false ) {
				checkout_enabled = false
			}

			awc_checkout.billing_address = billing_validation_response.address
		}

		awc_checkout.gateway_provider.enable(checkout_enabled);

	},

	nextPage: function() {
		var $page = $('.panel:visible');
		awc_checkout.showPage($page.next());
	},

	setupPage: function() {
		$('.panel .btn-next').click(awc_checkout.nextPage);

		// map address "edit" Button clicks ----------------------------

		$('#checkout-confirm-shipping .btn-primary')
			.click(function() {
				awc_checkout.showPage('#checkout-shipping');
			})
		$('#checkout-confirm-billing .btn-primary')
			.click(function() {
				awc_checkout.showPage('#checkout-billing');
			})

		// map breadcrumb clicks ---------------------------------------
		$('#bc-shipping').click(function(e) { e.preventDefault(); awc_checkout.showPage('#checkout-shipping'); });
		$('#bc-billing').click(function(e) { e.preventDefault(); awc_checkout.showPage('#checkout-billing'); });
		$('#bc-checkout').click(function(e) { e.preventDefault(); awc_checkout.showPage('#checkout-confirmation'); });
		$('#bc-shipping-method').click(function(e) { e.preventDefault(); awc_checkout.showPage('#checkout-shipping-method'); });

		// create a full cart feed from awesom cart js
		cart.newCartFeed('cart-full', {
			container: '#cart-full',
			tpl: cart.template('cart-full')
		})

		function onCartChanges() {

			// FIX: Babelfish issue, cart.totalItems getter not invoked in IF statement
			var totalItems = cart.totalItems;
			// make sure panels are visible once cart is processed and has items
			if ( totalItems > 0 ) {
				$('#checkout-panels').fadeIn('fast')
			} else {
				$('#checkout-panels').hide()

			}
		}

		cart.on('init', onCartChanges);
		cart.on('update', onCartChanges);

		cart.on('init', function() {
			// handle smart placeholder labels
			$('.awc-form .field').each(function() {
				var $field = $(this);
				var $input = $(this).find('input:first, select:first');

				$input
					.change(function() {
						if ( $(this).val() ) {
							$field.addClass('hasvalue');
						} else {
							$field.removeClass('hasvalue');
						}
					})
					.keyup(function() {
						if ( $(this).val() ) {
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
			});
		})
	}
}

awc_checkout.setupPage();
