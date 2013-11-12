function(modal) {
	modal.respond('creditUpdated', '{{ credits_html|escapejs }}');
	modal.close();
}
