(function($) {
    $.fn.extractNickMatchData = function() {
        var context = this.get(0);
        var searchTermField = $('input[type=hidden]', context);
        var fieldPrefix = searchTermField.attr('name').replace(/name$/, '');

        var name = searchTermField.val();
        var choices = [];
        var id;
        $('> ul > li', this).each(function(i) {
            /* nameWithAffiliations = content of the <label> element excluding child elements (i.e. only including text nodes, nodeType=3) */
            var nameWithAffiliations = $('label', this).contents().filter(function() { return this.nodeType == 3; }).text();

            var input = $('input', this);
            if (input.is(':checked')) {
                id = input.attr('value');
            }
            choices[i] = {
                className: $(this).attr('class'),
                nameWithDifferentiator: $(this).attr('data-name'),
                nameWithAffiliations: nameWithAffiliations.trim(),
                countryCode: $('img[data-countrycode]', this).attr('data-countrycode'),
                differentiator: $('.differentiator', this).text().replace(/^\((.*)\)$/, '$1'), /* strip outer brackets */
                alias: $('.alias', this).text(),
                id: $('input', this).val()
            };
        });
        return {
            'selection': {'id': id, 'name': name},
            'choices': choices,
            'fieldPrefix': fieldPrefix
        };
    };

    $.fn.nickMatchWidget = function() {
        this.each(function() {
            var context = this;

            var matchData = $(context).extractNickMatchData();
            NickMatchWidget(context, matchData.selection, matchData.choices, matchData.fieldPrefix);
        });
    };
})(jQuery);

function NickMatchWidget(elem, nickSelection, choices, fieldPrefix) {
    var self = {};
    var $elem = $(elem);

    $elem.empty();

    var selectedResult = $('<a href="javascript:void(0)" tabindex="0" class="selected_result"></a>');
    /* tabindex ensures that a click causes it to be focused on Chrome */
    var selectedResultInner = $('<span></span>');
    selectedResult.append(selectedResultInner);
    selectedResultInner.text(nickSelection.name);

    var suggestionsUl = $('<ul></ul>');
    for (var i = 0; i < choices.length; i++) {
        var choice = choices[i];
        var li = $('<li></li>').attr({
            'class': choice.className,
            'data-name': choice.nameWithDifferentiator
        });
        var label = $('<label></label>').text(choice.nameWithAffiliations);
        if (choice.countryCode) {
            var flag = $('<img />').attr({
                'src': '/static/images/icons/flags/' + choice.countryCode + '.png',
                'data-countrycode': choice.countryCode,
                'alt': '(' + choice.countryCode.toUpperCase() + ')'
            });
            label.prepend(flag, ' ');
        }

        var input = $('<input type="radio" />').attr({
            'name': fieldPrefix + 'id',
            'value': choice.id
        });
        if (nickSelection.id == choice.id) input.attr('checked', 'checked');
        label.prepend(input);

        if (choice.differentiator) {
            var differentiator = $('<em class="differentiator"></em>').text('(' + choice.differentiator + ')');
            label.append(' ', differentiator);
        }

        if (choice.alias) {
            var alias = $('<em class="alias"></em>').text('(' + choice.alias + ')');
            label.append(' ', alias);
        }

        li.append(label);
        suggestionsUl.append(li);
    }

    var searchTermField = $('<input type="hidden" />').attr({
        'name': fieldPrefix + 'name',
        'value': nickSelection.name
    });

    $elem.append(selectedResult, suggestionsUl, searchTermField);

    function copyIconFromSelectedLi() {
        /* inherit icon for selectedResult from the li with the selected radio button,
        or 'error' icon if there is none */
        var selectedLi = $('li:has(input:checked)', suggestionsUl);
        if (selectedLi.length) {
            var classNames = 'selected_result ' + selectedLi.attr('class');
            if (selectedResult.hasClass('active')) classNames += ' active';
            selectedResult.attr('class', classNames);
            /* also copy label text from the data-name attribute */
            selectedResultInner.text(selectedLi.attr('data-name'));
        } else {
            selectedResult.attr('class', 'selected_result error');
        }
    }
    copyIconFromSelectedLi();

    function highlightSelectedLi() {
        $('li', suggestionsUl).removeClass('selected');
        $('li:has(input:checked)', suggestionsUl).addClass('selected');
    }

    function keypress(e) {
        if (e.which == 40) { /* cursor down */
            if (suggestionsUl.is(':visible')) {
                var nextElem = $('li:has(input:checked)', suggestionsUl).next();
                if (nextElem.length) {
                    $('input', nextElem).attr('checked', 'checked');
                } else {
                    $('li:first input', suggestionsUl).attr('checked', 'checked');
                }
                highlightSelectedLi();
                copyIconFromSelectedLi();
            } else {
                suggestionsUl.show();
            }
            return false;
        } else if (e.which == 38) { /* cursor up */
            if (suggestionsUl.is(':visible')) {
                suggestionsUl.show();
                var prevElem = $('li:has(input:checked)', suggestionsUl).prev();
                if (prevElem.length) {
                    $('input', prevElem).attr('checked', 'checked');
                } else {
                    $('li:last input', suggestionsUl).attr('checked', 'checked');
                }
                highlightSelectedLi();
                copyIconFromSelectedLi();
            } else {
                suggestionsUl.show();
            }
            return false;
        } else if (e.which == 13) { /* enter */
            /* show/hide the dropdown.
                Serves no purpose, but seems to be psychologically important. UI design, eh? */
            if (suggestionsUl.is(':visible')) {
                suggestionsUl.hide();
            } else {
                suggestionsUl.show();
            }
        }
    }

    var suppressCloseDropdown = false;
    function closeDropdown() {
        selectedResult.removeClass('active');
        suggestionsUl.hide();
        copyIconFromSelectedLi();
        $(document).unbind('keydown', keypress);
        suppressCloseDropdown = false;
    }

    suggestionsUl.hide();
    suggestionsUl.mousedown(function() {
        suppressCloseDropdown = true;
        $(document).one('mouseup', function() {
            setTimeout(closeDropdown, 100);
        });
    });
    var wasFocusedOnLastMousedown = false;
    selectedResult.focus(function() {
        selectedResult.addClass('active');
        suggestionsUl.show();
        highlightSelectedLi();
        $(document).bind('keydown', keypress);
    }).blur(function() {
        if (suppressCloseDropdown) return false;
        setTimeout(closeDropdown, 100);
    }).click(function() {
        if (selectedResult.hasClass('active') && wasFocusedOnLastMousedown) {
            selectedResult.blur();
        }
    }).mousedown(function() {
        wasFocusedOnLastMousedown = selectedResult.hasClass('active');
    });

    $elem.addClass('nick_match--ajaxified');

    self.isValid = function() {
        var id = suggestionsUl.find('input:checked').val();
        return (id !== null);
    };
    self.getSelection = function() {
        var id = suggestionsUl.find('input:checked').val();
        /* id=null indicates nothing selected (i.e. ambiguous name) */
        return {'id': id, 'name': nickSelection.name};
    };
    self.getValue = function() {
        return {
            'selection': self.getSelection(),
            'choices': choices
        };
    };

    return self;
}
