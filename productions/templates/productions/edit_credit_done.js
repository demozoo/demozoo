function(modal) {
    modal.respond('creditsUpdated', '{{ credits_html|escapejs }}');
    modal.close();
}
