function htmlEncode(str) {
	return str.replace(/&/g,'&amp;').replace(/>/g,'&gt;').replace(/</g,'&lt;').replace(/"/g,'&quot;');
}

function applyGlobalBehaviours(context) {
	$('ul.messages li', context).animate({'backgroundColor': 'white'}, 5000);

	$('a.open_in_lightbox', context).click(function(e) {
		if (e.ctrlKey || e.altKey || e.shiftKey || e.metaKey || e.which === 2) {
			/* probably means they want to open it in a new window, so let them... */
			return true;
		}
		var focusEmptyInput = $(this).hasClass('focus_empty_input');
		Lightbox.openUrl(this.href, applyGlobalBehaviours, {'focusEmptyInput': focusEmptyInput});
		return false;
	});
	$('form.open_in_lightbox', context).submit(function() {
		/* only use this for forms with method="get"! */
		Lightbox.openUrl(this.action + '?' + $(this).serialize(), applyGlobalBehaviours);
		return false;
	});

	$('.microthumb', context).thumbPreview();
}

$(function() {
	var loginLinks = $('#login_status_panel .login_links');
	
	loginLinks.hide();
	var loginLinksVisible = false;
	
	function hideLoginLinksOnBodyClick(e) {
		if (loginLinksVisible && !loginLinks.has(e.target).length) {
			loginLinks.hide(); loginLinksVisible = false;
		}
	}
	function showLoginLinks() {
		loginLinks.slideDown(100);
		loginLinksVisible = true;
		$('body').bind('click', hideLoginLinksOnBodyClick);
	}
	function hideLoginLinks() {
		loginLinks.hide();
		loginLinksVisible = false;
		$('body').unbind('click', hideLoginLinksOnBodyClick);
	}
	
	$('#login_status_panel .login_status').wrapInner('<a href="javascript:void(0)"></a>');
	$('#login_status_panel .login_status a').click(function() {
		if (loginLinksVisible) {
			hideLoginLinks();
		} else {
			showLoginLinks();
		}
		return false;
	});

	var searchPlaceholderText = 'Type in keyword';
	var searchField = $('#global_search #id_q');
	if (searchField.val() === '' || searchField.val() === searchPlaceholderText) {
		searchField.val(searchPlaceholderText).addClass('placeholder');
	}
	searchField.focus(function() {
		if (searchField.hasClass('placeholder')) {
			searchField.val('').removeClass('placeholder');
		}
	}).blur(function() {
		if (searchField.val() === '') {
			searchField.val(searchPlaceholderText).addClass('placeholder');
		}
	});
	$('#global_search').submit(function() {
		if (searchField.hasClass('placeholder') || searchField.val() === '') {
			searchField.focus(); return false;
		}
	});

	searchField.autocomplete({
		'html': true,
		'source': function(request, response) {
			$.getJSON('/search/live/', {'q': request.term}, function(data) {
				for (var i = 0; i < data.length; i++) {
					var thumbnail = '';
					if (data[i].thumbnail) {
						thumbnail = '<div class="microthumb"><img src="' + htmlEncode(data[i].thumbnail.url) + '" width="' + data[i].thumbnail.width + '" height="' + data[i].thumbnail.height + '" alt="" /></div>';
					}
					data[i].label = '<div class="autosuggest_result ' + htmlEncode(data[i].type) + '">' + thumbnail + htmlEncode(data[i].value) + '</div>';
				}
				response(data);
			});
		},
		'select': function(event, ui) {
			document.location.href = ui.item.url;
		}
	});
    
	searchField.data("autocomplete")._renderItem = function( ul, item ) {
		return $( "<li></li>" )
			.data( "item.autocomplete", item )
			.append( $( "<a></a>" ).html(item.label).attr("href",item.url) )
			.appendTo( ul );
	};

	applyGlobalBehaviours();
});
