function initEditChunkHover(context) {
	$('.edit_chunk', context).hover(function() {
		$(this).closest('.editable_chunk').addClass('hover');
	}, function() {
		$(this).closest('.editable_chunk').removeClass('hover');
	});
}

$(function() {
	initEditChunkHover();
});
