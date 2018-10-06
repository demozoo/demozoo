$(function() {
	constructMatchingInterface({
		'leftSelector': 'button.demozoo_prod',
		'rightSelector': 'button.pouet_prod',
		'unlinkAction': function(leftVal, rightVal) {
			$.ajax({
				type: 'POST',
				url: '/pouet/unlink/',
				data: {'demozoo_id': leftVal, 'pouet_id': rightVal},
				beforeSend: function(xhr) {
					/* need to add CSRF token to the request so that Django will accept it */
					xhr.setRequestHeader('X-CSRFToken', $.cookie('csrftoken'));
				}
			});
		},
		'leftListSelector': 'ul.unmatched_demozoo_prods',
		'rightListSelector': 'ul.unmatched_pouet_prods',
		'linkAction': function(leftVal, rightVal) {
			/* post the ID pair to the server */
			$.ajax({
				type: 'POST',
				url: '/pouet/link/',
				data: {'demozoo_id': leftVal, 'pouet_id': rightVal},
				beforeSend: function(xhr) {
					/* need to add CSRF token to the request so that Django will accept it */
					xhr.setRequestHeader('X-CSRFToken', $.cookie('csrftoken'));
				}
			});
		}
	});
});
