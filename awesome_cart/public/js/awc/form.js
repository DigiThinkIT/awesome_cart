frappe.provide("awc");

awc.Form = Class.extend({
	init: function($form) {
		var scope = this;
		this.$form = $form;

		this.$form.data("awc_form", this);
		
		// Dynamically display selector on field value change
		this.$form.find('[data-display-on-val]').each(function() {
			var selector = $(this).attr("data-display-on-val");
			var $base = $(this);
			$(selector).change(function() {
			var toggleValue = false;
			if ( $(this).is(':checkbox') ) {
				toggleValue = $(this).is(':checked');
			} else {
				toggleValue = $(this).val()?true:false;
			}

			if ( toggleValue ) {
				$base.slideDown('fast');
			} else {
				$base.slideUp('fast');
			}
			});
			$(this).hide();
		});


		// Dynamically display selector on field value change
		this.$form.find('[data-display-on-val]').each(function() {
			var selector = $(this).attr("data-display-on-val");
			var $base = $(this);
			$(selector).change(function() {
			var toggleValue = false;
			if ( $(this).is(':checkbox') ) {
				toggleValue = $(this).is(':checked');
			} else {
				toggleValue = $(this).val()?true:false;
			}

			if ( toggleValue ) {
				$base.slideDown('fast');
			} else {
				$base.slideUp('fast');
			}
			});
			$(this).hide();
		});

		// Dynamically add field to required fields on field value change
		this.$form.find('[data-required-on-val]').each(function() {
			var selector = $(this).attr("data-required-on-val");
			var $base = $(this);
			$(selector).change(function() {
				var toggleValue = false;
				if ( $(this).is(':checkbox') ) {
					toggleValue = $(this).is(':checked');
				} else {
					toggleValue = $(this).val()?true:false;
				}

				if ( toggleValue ) {
					$base.addClass('required');
				} else {
					$base.removeClass('required');
				}

				$base.find('.awi').trigger('blur');
			});
		});

		// Handle pay button click
		this.$form.find('.btn-primary').click(function() {
			var $form = $(this).closest('.dti-form');
			if ( $form.hasClass('incomplete') ) {
				$form.find('.required .awi').each(function() {
					if ( !$(this).val() ) {
					$(this).closest('.required:first').addClass('error');
					}
				});

				return;
			}

			$(this).trigger('submit_action');
		});

		// Setup field required values check
		this.$form.find('.field .awi').on('blur', function() { scope.check_required(false, $(this).closest('.field')); });
		this.$form.filter('[data-on-visible-focus]').each(function() {
			var $form = $(this);
			$form.data('last_visible', $form.is(':visible'));

			// watch for visible status change
			setInterval(function() {
				if ( $form.is(':visible') 
					&& $form.is(':visible') != $form.data('last_visible') ) {

					var focus_selector = $form.attr('data-on-visible-focus');
					var $el = $form.find(focus_selector);
					if ( $el.length > 0 ) {
						if ( $el.hasClass('field') ) {
							$el = $el.find('.awi');
						}
						$el.focus();
					}
				}
				$form.data('last_visible', $form.is(':visible'));

			}, 200);
		});

		this.check_required(false);
	},

	// Handler, used to check if required fields are filled to
	// enable/disable pay button.
	check_required: function(update_ui, $current_field) {

		if ( update_ui == undefined ) {
			update_ui = true;
		}

		var result = this.get_fields(update_ui, $current_field);
		var all_required_filled = result.valid;

		if ( all_required_filled ) {
			this.$form.removeClass('incomplete');
		} else {
			this.$form.addClass('incomplete');
		}
	},

	get_fields: function(update_ui, $current_field) {
		if ( update_ui == undefined ) {
			update_ui = false;
		}

		if ( $current_field == undefined ) {
			$current_field = false;
		}

		var fields = {};
		var all_required_filled = true;
		this.$form.find('.field .awi').each(function() {
			var $this = $(this);
			fields[$this.attr('name')] = $this.val();

			if ( $this.closest('.field').hasClass('required') && !$this.val() ) {
				all_required_filled = false;
			}

			if ( update_ui || $this.closest('.field').is($current_field) ) {
				if ( $this.closest('.field').hasClass('required') ) {
					if ( $this.val() ) {
						$this.closest(".required").removeClass("error");
					} else {
						$this.closest(".required").addClass("error");
					}
				} else {
					$this.closest('.field').removeClass("error");
				}
			}
		});
		
		return { valid: all_required_filled, fields: fields };

	},

});

