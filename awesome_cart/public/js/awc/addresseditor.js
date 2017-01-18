frappe.provide("awc");

awc.AddressEditor = Class.extend({
	init: function($el) {
		var scope = this;
		this.$el = $el;
		this.primary_field = $el.attr('data-primary-field');
		this.$content = $el.find('.content');
		this.prefix = $el.attr('data-field-prefix');
		this.$reditor = new awc.RadioEditor($el.find('.awc-radio-editor'), $el.find('.extra-actions'), this.formatter.bind(this), "New Address");
		this.$reditor.$el.on('option-select option-edit option-remove', function(e, value, record, mode) {
			console.log(this, value, record, mode);
			if ( value == 'new' ) {
				scope.update_fields({
					address_id: '',
					address_title: '',
					company: '',
					address_line1: '',
					address_line2: '',
					country: '',
					city: '',
					state: '',
					pincode: '',
					phone: ''
				});
				scope.lock_fields(false, false);
			} else {
				scope.update_fields(record);

				if ( mode == "select" ) {
					scope.lock_fields(true, true);
				} else if ( mode == "edit" ) {
					scope.lock_fields(false, false);
				} else if ( mode == "remove" ) {
					// Record was removed
				}
			}
		});

		// trigger fetching data after page load
		$(function() { scope.$reditor.update(); });
		this.$fields = {
			address_id: $el.find('[name=' + this.prefix + 'address_id]'),
			address_title: $el.find('[name=' + this.prefix + 'address_title]'),
			company: $el.find('[name=' + this.prefix + 'company]'),
			address1: $el.find('[name=' + this.prefix + 'address_1]'),
			address2: $el.find('[name=' + this.prefix + 'address_2]'),
			country: $el.find('[name=' + this.prefix + 'country]'),
			city: $el.find('[name=' + this.prefix + 'city]'),
			state: $el.find('[name=' + this.prefix + 'state]'),
			zip: $el.find('[name=' + this.prefix + 'zip]'),
			phone: $el.find('[name=' + this.prefix + 'phone]')
		};
	},

	update: function() {
		this.$reditor.update();
	},

	clip_text: function (text, max_length, elipsis) {
		if ( elipsis === undefined ) {
			elipsis = "";
		}

		text_elipsis = "";
		if ( text.length > max_length ) {
			text_elipsis = elipsis;
		}
		
		// do't cut words, move max length to next blank space
		if ( text.substring(max_length, 1) != " " ) {
			max_length += text.substring(max_length).indexOf(" ");
		}

		text = text.substring(0, max_length) + text_elipsis;

		return text;
	},

	get_address_label: function(r, max_length, elipsis) {
		var primary = (r[this.primary_field]?'<span class="special">(PRIMARY)</span>':'');
		if ( primary.length > 0 ) {
			max_length -= 9;
		}

		var title = this.clip_text(r.address_title, max_length, elipsis);
		var special = (r.address_title?'<span class="address_title">' + title + ' | </span>':'');
		if ( special.length > 0 ) {
			max_length -= title.length;
		}

		if ( max_length <= 0 ) {
			max_length = 0;
		}

		var label = "";
		
		if ( max_length > 0 ) {
			label += (r.address_line1?r.address_line1 + " ":"");
			label += (r.address_line1?r.address_line2 + " ":"");
			label += (r.city?r.city + ", ":"");
			label += (r.state?r.state + " ":"");
			label += (r.pincode?r.pincode + " ":"");

			label = this.clip_text(label, max_length, elipsis);
			label = '<span class="address">' + label + '</span>';
		}

		return primary + special + label;
	},

	formatter: function(r) {
		return {
			selected: r[this.primary_field],
			value: r.name,
			label: this.get_address_label(r, 40, ' ...'),
			detail: '<address>' +
					(r.address_line1?r.address_line1 + '<br>':'') +
					(r.address_line2?r.address_line2 + '<br>':'') +
					((r.city || r.state || r.pincode)?(r.city?r.city + ', ':'') + (r.state?r.state + ' ':'') + r.pincode + '<br>':'') +
					r.country +
				'</address>'
		}
	},
	update_fields: function(r) {

		if ( r ) {
			this.$fields.address_id.val(r.name);
			this.$fields.address_title.val(r.address_title);
			this.$fields.company.val(r.company);
			this.$fields.address1.val(r.address_line1);
			this.$fields.address2.val(r.address_line2);
			this.$fields.country.val(r.country);
			this.$fields.city.val(r.city);
			this.$fields.state.val(r.state);
			this.$fields.zip.val(r.pincode);
			this.$fields.phone.val(r.phone);

			return true;
		}

		return false;
	},
	lock_fields: function(lock, hide) {
		if ( lock === undefined ) {
			lock = true;
		}

		if ( hide === undefined ) {
			hide = false;
		}

		var blured = false;
		$.each(this.$fields, function(i, $f) {
			$f.prop('disabled', lock?true:false);
			if ( lock ) {
				$f.closest('.field').addClass('locked');
			} else {
				$f.closest('.field').removeClass('locked');
			}

			if ( !blured) { $f.blur(); blured = true; }
		});

		if ( hide ) {
			this.$content.slideUp('fast');
		} else {
			this.$content.slideDown('fast');
		}
	},

	delete_address: function(id) {
		
	}

});
