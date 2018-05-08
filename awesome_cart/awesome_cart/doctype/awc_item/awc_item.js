// Copyright (c) 2016, DigitThinkIt, Inc. and contributors
// For license information, please see license.txt

frappe.ui.form.on('AWC Item', {
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
					'<div class="control-input-wrapper form-control" style="min-height: 1em; cursor: text;">'+
						'<div class="tags-it-control">'+
						'</div>'+
					'</div>'+
				'</div>');

		var $tag_control = $(".frappe-control[data-fieldname=\"tags_html\"] .tags-it-control");
		var tag_control = new awc.ui.TagControl($tag_control.get(0), {
			placeholder: "Add a category...",
			source: function(value, response) {
				frappe.call({
					method: "awesome_cart.desk.get_categories",
					args: {
						term: value.toLowerCase()
					},
					callback: function(result) {
						// setup tag-it with resulting tags
						response(result.message);
					}
				})
			},
			onChange: function(e, tags) {
				if ( tags ) {
					frm.set_value("tags", tags.join(','));
				}
			}
		});

		$tag_control.data("tag_control", tag_control);

		$tag_control.closest(".form-control").click(function() {
			$tag_control.focus();
		})

	},

	refresh: function(frm) {

		var $tag_control = $(".frappe-control[data-fieldname=\"tags_html\"] .tags-it-control");
		var tag_control = $tag_control.data("tag_control");

		// build tag list
		var found_tags=[];
		if ( typeof frm.doc.tags === "string" ) {
			tag_control.refresh(frm.doc.tags.split(','));
		}

		frm.set_query("item_name", "recomendations", function () {
			return {
				"query": "awesome_cart.awesome_cart.doctype.awc_item.awc_item.query_items_with_awc_items"
			};
		});

	}
});
