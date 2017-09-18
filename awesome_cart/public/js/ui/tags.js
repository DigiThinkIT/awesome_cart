frappe.provide("awc.ui");

awc.ui.TagControl = Class.extend({
	init: function(element, config) {
		var base = this;
		this.$el = $(element);
		this.$el.addClass("awc-ui awc-tags");

		this.config = config;
		this.taggle_config = {
			placeholder: config.placeholder || undefined,
			onTagAdd: this.onTagAdd.bind(this),
			onTagRemove: this.onTagRemove.bind(this),
		};

		this.awesomplete_config = {
			minChars: 0,
			maxItems: 99,
			list: []
		}
		// setup taggle
		this.taggle = new Taggle(element, this.taggle_config);

		// setup awesomplete
		var input = this.taggle.getInput();
		var $input = this.$input = $(input);
		this.awesomplete = new Awesomplete(input, this.awesomplete_config);

		$input.on("awesomplete-open", function(e){
			$input.attr('state', 'open');
		});

		$input.on("awesomplete-close", function(e){
			$input.attr('state', 'closed');
		});

		$input.on("input", function(e) {
			var value = e.target.value;
			if ( typeof base.config.source === "function" ) {
				base.config.source(value, function(response) {
					base.awesomplete.list = response;
				})
			}
		});

		$input.on("focus", function(e) {
			if($input.attr('state') != 'open') {
				$input.trigger("input");
			}
		});
	},

	onTagAdd: function(e, tag) {
		if ( typeof this.config.onTagAdd === "function" ) {
			this.config.onTagAdd(e, tag);
		}
		if ( typeof this.config.onChange === "function" ) {
			this.config.onChange(e, this.taggle.getTagValues());
		}
	},

	onTagRemove: function(e, tag) {
		if ( typeof this.config.onTagRemove === "function" ) {
			this.config.onTagRemove(e, tag);
		}
		if ( typeof this.config.onChange === "function" ) {
			this.config.onChange(e, this.taggle.getTagValues());
		}
	},

	onAwesompleteInput: function(e) {
		var value = e.target.value;
	},

	refresh: function(tags) {
		this.taggle.removeAll();
		this.taggle.add(tags);
	},

	focus: function() {
		this.$input.focus();
	}
});
