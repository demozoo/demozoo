function(modal) {
	modal.respond('creditAdded', '{{ credits_html|escapejs }}');
	modal.close();
}
