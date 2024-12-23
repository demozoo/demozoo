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

    $('select[multiple]', context).asmSelect();

    $('input.date', context).each(function() {
        var opts = {dateFormat: 'd M yy', constrainInput: false, showOn: 'button', firstDay: 1, dateParser: parseFuzzyDate};
        $(this).datepicker(opts);
    });

    $('input.production_autocomplete', context).autocomplete({
        'source': function(request, response) {
            $.getJSON('/productions/autocomplete/', {'term': request.term}, function(data) {
                response(data);
            });
        },
        'autoFocus': true,
        'select': function(event, ui) {
            $('input#id_production_id').val(ui.item.id);
        }
    });

    $('[data-byline-field]', context).bylineField();

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
            'html': true,
            'source': function(request, response) {
                $.getJSON('/productions/autocomplete/',
                    {'term': request.term, 'supertype': titleField.attr('data-supertype')},
                    function(data) {
                        for (var i = 0; i < data.length; i++) {
                            data[i].label = '<div class="autosuggest_result ' + data[i].supertype + '">' + htmlEncode(data[i].label) + '</div>';
                        }
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
        $('.party_field_lookup', this).remove();
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

    $('[data-nick-match]', context).nickMatchWidget();

    $('[data-nick-field]', context).each(function() {
        var nickFieldElement = this;
        var nickField = $(this);
        var uid = $.uid('nickfield');
        
        var searchParams = {};
        if (nickField.hasClass('sceners_only')) searchParams['sceners_only'] = true;
        if (nickField.hasClass('groups_only')) searchParams['groups_only'] = true;
        var groupIds = nickField.data('group_ids');
        if (groupIds) searchParams['group_ids'] = groupIds;

        $('.nick_search input:submit', nickFieldElement).hide();
        var searchField = $('.nick_search input:text', nickFieldElement);
        var searchFieldElement = searchField.get(0);
        searchField.attr('autocomplete', 'off');
        var fieldPrefix = searchField.attr('name').replace(/_search$/, '_match_');
        var nickMatchContainer = $('.nick_match_container', nickFieldElement);
        
        searchField.typeahead(function(value, autocomplete) {
            if (value.match(/\S/)) {
                $.ajaxQueue(uid, function(release) {
                    /* TODO: consider caching results in a JS variable */
                    $.getJSON('/nicks/match/', $.extend({
                        q: value,
                        autocomplete: autocomplete
                    }, searchParams), function(data) {
                        if (searchField.val() == data['initial_query']) {
                            /* only update fields if search box contents have not changed since making this query */
                            nickMatchContainer.html('<div class="nick_match"></div>');
                            NickMatchWidget(
                                nickMatchContainer.find('.nick_match'),
                                data.match.selection, data.match.choices, fieldPrefix);
                            if (autocomplete) {
                                searchField.val(data.query);
                                if (searchFieldElement.setSelectionRange) {
                                    searchFieldElement.setSelectionRange(data['initial_query'].length, data.query.length);
                                    /* TODO: IE compatibility */
                                }
                            }
                        }
                        release();
                    });
                });
            } else {
                /* blank */
                nickMatchContainer.html('');
            }
        });
        
        $(this).addClass('nick_field--ajaxified');
    });
}

$(function() {
    applyEditControls($('[data-edit-form]'));
})
