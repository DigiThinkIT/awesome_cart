frappe.provide("awc");

awc.Form = Class.extend({
	init: function($form) {
		var scope = this;
		this._is_locked = false;
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
		this.$form.find('.btn-primary')
			.click(function() {
				var fields = scope.check_required(true); 
				if ( !fields.valid ) {
					return;
				}

				var done = function() {
					scope.on_action_wait(true);
				};

				var error = function(msg) {
					scope.on_action_error(msg);
				};

				scope.on_action_wait();
				scope.$form.trigger('submit_action', [fields, done, error]);
			});

		this.$form.find('.btn')
			.not('.btn-primary')
			.click(function() {
				scope.$form.trigger('awc_action', $(this));
			});

		this.$form.find('.field .awi')
			.on('blur keyup change', function(e) { 
				var keyCode = e.keyCode || e.which;
				var $field = $(this).closest('.field');
				if ( e.type == 'keyup' ) {
					if ( keyCode != 9 ) {
						scope.check_required(false, true); 
						if ( keyCode == 13 && $field.is('.submit-on-enter') ) {
							scope.$form.find('.btn-primary').click();
						}
					}
				} else {
					scope.check_required(false, true, $field); 
				}
			});

		this.$form.filter('[data-on-visible-focus]')
			.each(function() {
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

		this.check_required(false, false);
	},

	lock_fields: function(lock) {
		if ( lock === undefined ) {
			lock = true;
		}

		var fields = this.get_fields();
		this.$form.find('.field .awi').each(function() {
			var $f = $(this);
			$f.prop('disabled', lock?true:false);
			if ( lock ) {
				$f.closest('.field').addClass('locked');
			} else {
				$f.closest('.field').removeClass('locked');
			}
		});

		this._is_locked = lock;
	},

	on_validate: function(result) {
		return result; // default implementation just passes through results.
	},

	validate: function(update_ui, ignore_focused, $update_field) {
		// alias method for future renaming
		return this.check_required(update_ui, ignore_focused, $update_field);
	},

	// Handler, used to check if required fields are filled to
	// enable/disable pay button.
	check_required: function(update_ui, ignore_focused, $update_field) {

		if ( update_ui == undefined ) {
			update_ui = true;
		}

		var result = this.get_fields(update_ui, ignore_focused, $update_field);
		// Allow extending class to validate further
		result = this.on_validate(result);

		if ( result.valid ) {
			this.$form.removeClass('incomplete');
		} else {
			this.$form.addClass('incomplete');
		}

		return result;
	},

	get_fields: function(update_ui, ignore_focused, $update_field) {
		if ( update_ui == undefined ) {
			update_ui = false;
		}

		if ( ignore_focused == undefined ) {
			ignore_focus = true;
		}

		if ( $update_field == undefined ) {
			$update_field = false;
		}

		var fields = {};
		var all_required_filled = true;
		var fields_meta = {};
		this.$form.find('.field .awi').each(function() {
			var $this = $(this);
			var $field = $(this).closest('.field');

			var has_value = false;
			var field_value = $this.val();
			var field_human_value = field_value;
			var field_name = $this.attr('name');
			var type = $this.attr('type');

			if ( $this.is(':checkbox') ) {
				if ( $this.is(':checked') ) {
					has_value = true;
				} else {
					field_value = null;
				}
			} else if ( $this.is(':radio') ) {
				var radio_group = $this.attr('name');
				var $group = $this.parent().parent().find('[name="'+radio_group+'"]:checked');

				console.log("Group", $this, $group);

				if ( $group.length > 0 ) {
					field_value = $group.val();
					has_value = true;

					if ( $group.attr('data-human-value') ) {
						field_human_value = $group.attr('data-human-value');
					} else {
						field_human_value = field_value;
					}
				} else {
					field_value = null;
				}
			} else {
				if ( $this.val() ) {
					has_value = true;
				}
			}

			if ( $this.is('select') ) {
				type = 'select';
				field_human_value = $this.find("option[value='"+field_value+"']").text();
			}

			fields_meta[field_name] = {
				type: $this.attr('type'),
				is_required: $this.closest(".required").length > 0,
				has_value: has_value,
				value: field_value,
				human_value: field_human_value,
				label: $field.attr('data-label')
			}

			fields[$this.attr('name')] = field_value;

			if ( $this.closest('.field').hasClass('required') && !has_value ) {
				all_required_filled = false;
			}

			if ( update_ui || 
				( !ignore_focused && $this.is(':focus')) ||
				$field.is($update_field) ) {
				
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
	
		return { valid: all_required_filled, fields: fields, meta: fields_meta };

	},

	on_action_error: function(msg) {
		var $error = this.$form.find('.action-error');
		if ( !msg ) {
			$error.slideUp('fast').empty();
		} else {
			$error.slideDown('fast');
			$error.html(msg);
		}
	},

	on_action_wait: function(reset) {
		var $error = this.$form.find('.action-error');
		var $actions = this.$form.find('.action-content');
		var $spinner = this.$form.find('.action-spinner');
		if ( reset ) {
			$actions.slideDown('slow')
			$spinner.slideUp('slow');
		} else {
			this.on_action_error(); // reset error msg
			$actions.slideUp('fast');
			$spinner.slideDown('fast');
		}
	}

});

