// Copyright (c) 2016, DigitThinkIt, Inc. and contributors
// For license information, please see license.txt

frappe.ui.form.on('AWC Item', {
	__tags: function(frm) {
		console.log(frm, frm.doc.__tags)
	},
	setup: function(frm) {
		$('.frappe-control[data-fieldname="tags_html"]').empty();

		// flag control as initialized
		$('.frappe-control[data-fieldname="tags_html"]').addClass('initialized');

		// setup tag-it
		$('.frappe-control[data-fieldname="tags_html"]')
			.append(
				'<div class="clearfix">'+
					'<div class="clearfix">'+
						'<label class="control-label">Category Tags</label>'+
					'</div>'+
					'<div class="control-input-wrapper form-control" style="height: initial; overflow: auto; cursor: text;">'+
						'<ul class="tags-it-control">'+
						'</ul>'+
					'</div>'+
				'</div>');

		var $tag_control = $('.frappe-control[data-fieldname="tags_html"] .tags-it-control');
		// update our tags field handler
		var changeEvent = function(e, ui) {
			if ( $tag_control.data("tags-refreshing") ) {
				return;
			}

			var value = $tag_control.tagit("assignedTags").join(',');
			frm.set_value("tags", value);
		}

		$tag_control
			.tagit({
				fieldName: "categories",
				showAutocompleteOnFocus: true,
				placeholderText: "Add a category...",
				preprocessTag: function(val) {
					return (!val)?"":val.toLowerCase();
				},
				afterTagAdded: changeEvent,
				afterTagRemoved: changeEvent
			});

		$tag_control.find("input").autocomplete({
			minLength: 0,
			minChar: 0,
			source: function(request, response) {
				frappe.call({
					method: "awesome_cart.desk.get_categories",
					args: {
						term: request.term.toLowerCase()
					},
					callback: function(result) {
						// setup tag-it with resulting tags
						response(result.message);
					}
				})
			},
			open: function() { $(this).attr('state', 'open'); },
			close: function() { $(this).attr('state', 'closed'); }
		})

		$('.frappe-control[data-fieldname="tags_html"] .form-control').click(function() {
			$tag_control.data("ui-tagit").tagInput.focus();
		})

	},

	refresh: function(frm) {

		var $tag_control = $('.frappe-control[data-fieldname="tags_html"] .tags-it-control');
		$tag_control.data("tags-refreshing", true);

		$tag_control.tagit("removeAll");
		// build tag list
		var found_tags=[];
		if ( typeof frm.doc.tags == 'string' ) {
			var tags_arr = frm.doc.tags.split(',');
			for( i in tags_arr) {
				var tag = tags_arr[i];
				$tag_control.tagit("createTag", tag);
			}
		}

		$tag_control.data("tags-refreshing", false);
	}
});
