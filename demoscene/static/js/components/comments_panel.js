$(function() {
	$('.comment_form_trigger').each(function() {
		var commentForm = $('.comment_form');
		commentForm.hide();
		$(this).wrapInner('<a href="javascript:void(0)"></a>');
		$('a', this).click(function() {
			if (commentForm.is(':visible')) {
				commentForm.slideUp();
			} else {
				commentForm.slideDown(function() {
					commentForm.find('textarea').focus();
				});
			}
		});
	});

	if (location.hash.match(/\#comment-\d+/)) {
		$(location.hash).css({'background-color': '#dfd'}).animate({'backgroundColor': '#eee'}, 3000);
	}
});
