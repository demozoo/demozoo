function applyEditControls(context) {
	var sortableFormsets = $('ul.sortable_formset', context);
	/* need to apply styling adjustments before spawningFormset to ensure the 'detached' LI gets styled too */
	$('li.sortable_item', sortableFormsets).prepend('<div class="ui-icon ui-icon-arrowthick-2-n-s" title="drag to reorder"></div>');
	$('li.sortable_item input[name$="-ORDER"]', sortableFormsets).hide();

	$('.spawning_formset', context).spawningFormset({onShow: applyEditControls});

	sortableFormsets.sortable({
		'items': 'li.sortable_item',
		'update': function(event, ui) {
			$('input[name$="-ORDER"]', this).each(function(i) {
				$(this).val(i+1);
			});
		},
		'cancel': ':input,option,a,label'
	});

	$('.byline_field', context).bylineField();

	$('.production_field', context).each(function() {
		var staticView = $("> .static_view", this);
		var formView = $("> .form_view", this);
		var idField = $("> .form_view > input[type='hidden'][name$='_id']", this);
		if (idField.val() != '') {
			formView.hide();
			staticView.show();
		} else {
			formView.show();
			staticView.hide();
		}
		var clearButton = $('<a href="javascript:void(0);" class="clear_button">clear</a>');
		clearButton.click(function() {
			staticView.hide();
			$(':input', formView).val('');
			$('.byline_search input:text', formView).blur(); /* force refresh */
			formView.show();
			try {$(':input:visible', formView)[0].focus();}catch(_){}
		});
		staticView.append(clearButton);
		
		var titleField = $('input.title_field', this);
		titleField.autocomplete({
			'source': function(request, response) {
				$.getJSON('/productions/autocomplete/',
					{'term': request.term, 'supertype': titleField.attr('data-supertype')},
					function(data) {
						response(data);
					});
			},
			'autoFocus': true,
			'select': function(event, ui) {
				var title = $('<b></b>');
				title.text(ui.item.value);
				$('.static_view_text', staticView).html(title);
				idField.val(ui.item.id);
				formView.hide();
				staticView.show();
			}
		});
	});

	$('.party_field', context).each(function() {
		var searchField = $('.party_field_search', this);
		var partyIdField = $('.party_field_party_id', this);
		var helpText = $('.help_text', this);
		$('.party_field_lookup', this).hide();
		searchField.autocomplete({
			'source': function(request, response) {
				$.getJSON('/parties/autocomplete/', {'term': request.term}, function(data) {
					response(data);
				});
			},
			'autoFocus': true,
			'select': function(event, ui) {
				partyIdField.val(ui.item.id);
			}
		});
		searchField.focus(function() {helpText.show();});
		searchField.blur(function() {
			setTimeout(function() {helpText.hide();}, 1);
		});
		helpText.hide();
		$(this).addClass('ajaxified');
	});
}
