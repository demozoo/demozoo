$(function() {
	var notesPanel = $('.notes_panel');
	var notes = notesPanel.find('.notes');

	if (notes.height() > 350) {
		notes.css({'padding-bottom': '48px'});

		notesPanel.css({'position': 'relative', 'height': '300px'});
		var readMore = $('<a href="javascript:void(0);">Read more...</a>');
		readMore.css({
			'position': 'absolute', 'bottom': '0px', 'display': 'block', 'font-size': '16pt',
			'width': '100%', 'background-color': 'rgba(255, 255, 255, 0.8)', 'text-align': 'center',
			'line-height': '48px'
		});
		notesPanel.append(readMore);
		readMore.toggle(function() {
			notesPanel.animate({'height': notes.height() + 'px'}, function() {
				notesPanel.css({'height': 'auto'});
			});
			readMore.text('Collapse text');
		}, function() {
			notesPanel.animate({'height': '300px'});
			readMore.text('Read more...');
		});
	}
});