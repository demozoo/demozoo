function(modal) {
	$('.yes_button', modal.body).click(function() {
		var form = $('form.confirmation_form');
		modal.postForm(form.attr('action'), form.serialize() + '&yes=Yes');
		return false;
	});
	$('.no_button', modal.body).click(function() {
		modal.close();
		return false;
	});
}
