frappe.provide("awc");

awc.RadioEditor = Class.extend({
	init: function($el, $actions, formatter, new_label) {

		if ( $el.length == 0 ) {
			console.log("Invalid jquery object", $el);
		}

		this.$el = $el
		this.$actions = $actions
		this.$container = $el.find('.data');
		this.formatter = formatter
		this.source = $el.attr('data-source');
		this.group = $el.attr('data-group');
		this.start = 0;
		this.limit = null;

		var btn_new_id = this.group + "-new-btn";
		this.$btn_new = $(
			'<div class="btn">'+
				'<input type="radio" id="'+btn_new_id+'" name="' + this.group + '" value="new"/>'+
				'<label for="'+btn_new_id+'">' + new_label + '</label>'+
			'</div>');

		this.$actions.append(this.$btn_new);
		this.$btn_new.hide();

		if ( !this.source ) {
			console.log("Invalid data source [empty]");
		}
	},

	get_options_el: function() {
		var options = this.$el.find('input[type=radio][name=' + this.group + ']');
		return options.add(this.$btn_new.find('input'));
	},

	select_option: function($el, mode) {

		$el.prop('checked', 'checked'); // make sure ui reflects change
		this.get_options_el().not($el).closest('label').removeClass('selected');
		$el.closest('label').addClass('selected');

		this.get_options_el().not($el).closest('label').find('.content').slideUp('fast');
		$el.closest('label').find('.content').slideDown('fast');
		this.$el.trigger('option-' + mode, [$el.val(), $el.data('record'), mode]);

	},

	remove: function(value) {
		var scope = this;
		if ( confirm("Remove this record permanently?") ) {
			frappe.call({
				method: this.source,
				args: { "address_id": value, "action": "remove" },
				callback: function(r) {
					var result = r.message;
					if ( result.success ) {
						scope.$container.find('label[data-value="' + value + '"]').remove();
						scope.update();
					} else {
						alert("There was an error removing this record.\n Please contact us and let us know of this issue.");
					}
				}});
		}
	},

	update: function() {
		var scope = this;
		frappe.call({
			method: this.source,
			args: { "start": this.start, "limit": this.limit },
			callback: function(r) {
				var result = awc.response(r);
				scope.$container.empty();
				if ( result.data === undefined || result.data.length == 0 ) {
					scope.$btn_new.fadeOut('fast');
				} else {
					scope.$btn_new.fadeIn('fast');
				}
				$selected = null;
				$.each(result.data, function(k, v) {
					var line = scope.formatter(v);
					var id = scope.group + "_" + line.value;
					var $option = $(
						'<label for="' + id + '" data-value="' + line.value + '">'+
							'<div class="row nohmargin" data-value="' + line.value + '">' +
								'<div class="col-md-12 nohpad">' +
									'<input type="radio" id="' + id +'" name="'+scope.group+'" value="' + line.value + '" />' +
									'<div class="label">' + line.label + '</div>'+
									'<div class="content">' + line.detail + '</div>'+
									'<div class="editor-actions">' +
										'<button class="btn btn-remove">Remove</button>' +
										'<button class="btn btn-edit">Edit</button>' +
									'</div>' +
								'</div>' +
							'</div>' +
						'</label>');
					scope.$container.append($option);
					if ( line.selected ) {
						$selected = $option;
					}
					$option.find('input').data('record', v);
					$option.find('input').data('record_id', line.value);
					$option.find('.btn-edit').click(function() {
						var $input = $(this).closest('label').find('input');
						scope.select_option($input, 'edit');
					});
					$option.find('.btn-remove').click(function() {
						var $input = $(this).closest('label').find('input');
						var record = $input.data('record');
						var record_id = $input.data('record_id');
						scope.remove(record_id, function() {
							scope.select_option(record, 'remove');
						});
					});
				});

				scope.get_options_el().off('change');
				scope.get_options_el().change(function() {
					var $checked = $(this).filter(':checked');
					if ( $checked.length > 0 ) {
						scope.select_option($checked, 'select');
					}
				});

				if ( $selected ) {
					scope.select_option($selected.find('input'), 'select');

				}
			}
		});
	}
});
