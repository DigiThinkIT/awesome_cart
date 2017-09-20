window.awc_utils = {

	user_addresses: null,

  get_user_addresses: function(done) {
		// gets user addresses then caches the values to be returned on follwing
		// calls to this method.

		if ( awc_utils.user_addresses == null ) {
			$(function() {

			awc.call("awesome_cart.utils.get_addresses")
				.then(function(r) {
					awc_utils.user_addresses = r.data.addresses;
					done(null, awc_utils.user_addresses);
				})
				.catch(function(err) {
					console.error(err);
					done(err, []);
				});

			});

		} else {
			done(null, awc_utils.user_addresses);
		}
	},

	render_address_widget: function(options) {
		return frappe.render_template("awc_address_form", options);
	},

	build_address_widget: function($container, options) {
		// options is required to contain the following keys:
		// addresses - array of addresses doctypes
		// label - a label to use to name buttons and titles
		// data_type - this address data type: bill/ship

		var tpl = awc_utils.render_address_widget(options);
		var $widget = $(tpl);
		$container.append($widget);

		$container.find(".addr").click(function(e) {
			e.stopPropagation();

			$container.find(".addr.selected").removeClass("selected");
			$(this).addClass('selected');
			if ( typeof options.on_address_click === "function" ) {
				options.on_address_click($(this), e);
			}
		});

		$container.find(".addr .edit").click(function(e) {
			if ( typeof options.on_address_edit === "function" ) {
				options.on_address_edit($(this), e);
			}
		})

		$container.find(".addr .delete").click(function(e) {
			if ( typeof options.on_address_delete === "function" ) {
				options.on_address_delete($(this), e);
			}
		})

		if ( typeof options.on_init === "function" ) {
			options.on_init($widget);
		}

	}

}
