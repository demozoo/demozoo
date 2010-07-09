function htmlEncode(str) {
	return str.replace(/&/g,'&amp;').replace(/>/g,'&gt;').replace(/</g,'&lt;').replace(/"/g,'&quot;');
}
	
$(function() {
	$('ul.messages li').animate({'backgroundColor': 'white'}, 5000);
	
	$('.spawning_formset').each(function() {
		var formset = this;
		var totalFormsInput = $("input[type='hidden'][name$='TOTAL_FORMS']", this);
		var fieldPrefix = totalFormsInput.attr('name').replace(/TOTAL_FORMS$/, '');
		
		function deleteForm(li) {
			$('.delete input:checkbox', li).attr('checked', true);
			$('> *', li).fadeOut(); /* fading out the LI itself is borked on Webkit (as of 2010-06-01) */
		}
		
		$('> ul > li', this).each(function() {
			var li = this;
			var deleteButton = $('<a href="javascript:void(0);" class="delete_button" title="delete">delete</a>');
			deleteButton.click(function() {
				deleteForm(li);
			});
			$('.delete', li).hide().after(deleteButton);
		});
		var lastElement = $('> ul > li:last', this);
		var newFormTemplate = lastElement.clone();
		var newFormInitialIndex = totalFormsInput.val() - 1;
		
		if (totalFormsInput.val() > 1 || $(this).hasClass('initially_hidden')) {
			lastElement.remove();
			totalFormsInput.val(totalFormsInput.val() - 1);
		}
		
		var addButton = $('<a href="javascript:void(0);" class="add_button">add</a>');
		var addLi = $('<li></li>');
		addLi.append(addButton);
		addButton.click(function() {
			var newForm = newFormTemplate.clone();
			addLi.before(newForm);
			var newIndex = parseInt(totalFormsInput.val());
			totalFormsInput.val(newIndex + 1);
			$(":input[name^='" + fieldPrefix + "']", newForm).each(function() {
				this.name = this.name.replace(fieldPrefix + newFormInitialIndex, fieldPrefix + newIndex);
			})
			$(":input[id^='id_" + fieldPrefix + "']", newForm).each(function() {
				this.id = this.id.replace('id_' + fieldPrefix + newFormInitialIndex, 'id_' + fieldPrefix + newIndex);
			})
			$("label[for^='id_" + fieldPrefix + "']", newForm).each(function() {
				this.htmlFor = this.htmlFor.replace('id_' + fieldPrefix + newFormInitialIndex, 'id_' + fieldPrefix + newIndex);
			})
			$('a.delete_button', newForm).click(function() {
				deleteForm(newForm);
			});
			newForm.hide().slideDown('fast');
			$(":input", newForm).focus();
		})
		$('> ul', this).append(addLi);
	})
	
	function addAutocompleteRule(selector, url, idField) {
		$(selector).autocomplete(url, {
			autoFill: true,
			formatItem: function(row) {return htmlEncode(decodeURIComponent(row[1]))},
			formatResult: function(row) {return decodeURIComponent(row[2])},
			selectFirst: true,
			matchSubset: false,
			matchCase: true,
			extraParams: {'new_option': true}
		}).result(function(evt, result) {
			$(idField).val(result[0]);
		});
	}
	addAutocompleteRule('input.group_autocomplete', '/groups/autocomplete/', 'input#id_group_id');
	addAutocompleteRule('input.scener_autocomplete', '/sceners/autocomplete/', 'input#id_scener_id');
	
	function parseAutocompleteResults(data) {
		var results = [];
		var resultLines = data.split(/\n/);
		for (var i = 0; i < resultLines.length; i++) {
			var resultFields = resultLines[i].split('|');
			if (resultFields.length > 1) {
				results.push({
					'id': resultFields[0],
					'label': decodeURIComponent(resultFields[1]),
					'name': decodeURIComponent(resultFields[2]),
					'score': parseInt(resultFields[3]),
					'icon': resultFields[4]
				})
			}
		}
		return results;
	}
	
	var previousAuthorSuggestions = {}
	function getAuthorSuggestions(name, groups, callback) {
		if (previousAuthorSuggestions[name] && previousAuthorSuggestions[name][groups]) {
			callback(previousAuthorSuggestions[name][groups]);
		} else {
			$.get('/releasers/autocomplete/', {
				'q': name, 'group': groups, 'exact': 'true', 'new_option': 'true'
			}, function(data) {
				var results = parseAutocompleteResults(data);
				if (!previousAuthorSuggestions[name]) previousAuthorSuggestions[name] = {};
				previousAuthorSuggestions[name][groups] = results;
				callback(results);
			})
		}
	}
	
	var previousGroupSuggestions = {}
	function getGroupSuggestions(name, members, callback) {
		if (previousGroupSuggestions[name] && previousGroupSuggestions[name][members]) {
			callback(previousGroupSuggestions[name][members]);
		} else {
			$.get('/groups/autocomplete/', {
				'q': name, 'member': members, 'exact': 'true', 'new_option': 'true'
			}, function(data) {
				var results = parseAutocompleteResults(data);
				if (!previousGroupSuggestions[name]) previousGroupSuggestions[name] = {};
				previousGroupSuggestions[name][members] = results;
				callback(results);
			})
		}
	}
	
	function suggestionsHaveTopResult(results) {
		if (results.length == 0) return false;
		if (results[0].score < 0) return false;
		if (results.length == 1) return true;
		return (results[0].score > results[1].score);
	}
	
	function buildAuthorMatchElement(author, results, container) {
		if (suggestionsHaveTopResult(results)) {
			var selectedResult = $('<a href="javascript:void(0)" class="selected_result"></a>');
			var selectedResultInner = $('<span></span>');
			selectedResult.append(selectedResultInner);
			selectedResult.addClass('icon_' + results[0].icon);
			selectedResultInner.text(results[0].label);
		} else {
			var selectedResult = $('<a href="javascript:void(0)" class="selected_result icon_error"></a>');
			var selectedResultInner = $('<span></span>');
			selectedResult.append(selectedResultInner);
			selectedResultInner.text(author);
		}
		container.append(selectedResult);
		var suggestionsUl = $('<ul class="suggestions"></ul>');
		for (var i = 0; i < results.length; i++) {
			var suggestionLi = $('<li></li>');
			var suggestionA = $('<a href="javascript:void(0)"></a>');
			suggestionLi.append(suggestionA);
			suggestionA.text(results[i].label).addClass('icon_' + results[i].icon);
			suggestionsUl.append(suggestionLi);
		}
		/* TODO: fake a selector bar that moves with up/down arrow keys, to make the list
		keyboard accessible */
		container.append(suggestionsUl);
		suggestionsUl.hide();
		selectedResult.click(function() {
			if ($(this).is('.active')) {
				$(this).blur();
			} else {
				$(this).focus();
			}
			return false;
		}).focus(function() {
			$(this).addClass('active');
			suggestionsUl.show();
		}).blur(function() {
			$(this).removeClass('active');
			suggestionsUl.hide();
		})
	}
	
	var lastByline;
	function parseByline() {
		var byline = $(this).val();
		if (byline == lastByline) return;
		lastByline = byline;
		/* try to split on the first '/' into authors and affiliations */
		var match = byline.match(/^(.+?)\/(.*)/)
		if (match) {
			/* split author / affiliation lists on standard separators: / + ^ , & */
			var rawAuthors = match[1].split(/[\/\+\^\,\&]/);
			var rawAffiliations = match[2].split(/[\/\+\^\,\&]/);
		} else {
			/* treat the entire thing as a list of authors */
			var rawAuthors = byline.split(/[\/\+\^\,\&]/);
			var rawAffiliations = [];
		}
		/* clean up list - strip leading/trailing whitespace and remove blank entries */
		var authors = [];
		var affiliations = [];
		for (var i = 0; i < rawAuthors.length; i++) {
			var author = rawAuthors[i].replace(/^\s+/, '').replace(/\s+$/, '')
			if (author != '') authors.push(author);
		}
		for (var i = 0; i < rawAffiliations.length; i++) {
			var affiliation = rawAffiliations[i].replace(/^\s+/, '').replace(/\s+$/, '')
			if (affiliation != '') affiliations.push(affiliation);
		}
		
		$('#matched_names').empty();
		/* TODO: detect if focus is on one of the elements being deleted, and prevent it from
		sending the tab index into outer space */
		if (authors.length || affiliations.length) {
			var matchedAuthorsUl = $('<ul></ul>');
			var matchedGroupsUl = $('<ul></ul>');
			$('#matched_names').append(
				'Matched names:',
				matchedAuthorsUl,
				matchedGroupsUl)
			
			$.each(authors, function(i, author) {
				var authorLi = $('<li class="matched_name"></li>');
				matchedAuthorsUl.append(authorLi);
				getAuthorSuggestions(author, affiliations, function(results) {
					buildAuthorMatchElement(author, results, authorLi);
				});
			});
			$.each(affiliations, function(i, affiliation) {
				var groupLi = $('<li class="matched_name"></li>');
				matchedGroupsUl.append(groupLi);
				getGroupSuggestions(affiliation, authors, function(results) {
					buildAuthorMatchElement(affiliation, results, groupLi);
				});
			});
		}
	}
	$('input#byline_autocomplete').blur(parseByline);
})
