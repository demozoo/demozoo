$(function() {
	constructMatchingInterface({
		'leftSelector': 'button.file',
		'rightSelector': 'button.production',
		'unlinkAction': function(leftVal, rightVal) {
			$.ajax({
				type: 'POST',
				url: '/sceneorg/compofiles/unlink/',
				data: {'file_id': leftVal, 'production_id': rightVal},
				beforeSend: function(xhr) {
					/* need to add CSRF token to the request so that Django will accept it */
					xhr.setRequestHeader('X-CSRFToken', $.cookie('csrftoken'));
				}
			});
		},
		'leftListSelector': 'ul.unmatched_files',
		'rightListSelector': 'ul.unmatched_productions',
		'linkAction': function(leftVal, rightVal) {
			/* post the ID pair to the server */
			$.ajax({
				type: 'POST',
				url: '/sceneorg/compofiles/link/',
				data: {'file_id': leftVal, 'production_id': rightVal},
				beforeSend: function(xhr) {
					/* need to add CSRF token to the request so that Django will accept it */
					xhr.setRequestHeader('X-CSRFToken', $.cookie('csrftoken'));
				}
			});
		}
	});
});
