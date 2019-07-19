$(function() {
	var matchingInterface;

	matchingInterface = constructMatchingInterface({
		'leftSelector': 'button.demozoo_prod',
		'initLeftButton': function() {
			var prodId = this.value;

			var infoLink = $('<a class="demozoo-info" title="Open this prod\'s Demozoo entry" target="_blank">info</button>');
			infoLink.attr('href', $(this).data('info-url'));
			$(this).after(infoLink);
		},

		'rightSelector': 'button.janeway_prod',
		'initRightButton': function() {
			var prodId = this.value;
			var rightButton = this;

			var infoLink = $('<a class="janeway-info" title="Open this prod\'s Kestra Bitworld entry" target="_blank">info</button>');
			infoLink.attr('href', $(this).data('info-url'));
			$(this).after(infoLink);

			if ($(this).hasClass('unmatched') && $(this).hasClass('importable')) {
				var importButton = $('<button class="import" title="Import into Demozoo">import</button>');
				infoLink.after(importButton);
				importButton.click(function() {
					$.ajax({
						type: 'POST',
						url: '/janeway/production-import/',
						data: {'janeway_id': prodId},
						beforeSend: function(xhr) {
							xhr.setRequestHeader('X-CSRFToken', $.cookie('csrftoken'));
						},
						success: function(data) {
							matchingInterface.removeRightButton(rightButton);
							matchingInterface.addMatchElement($(data));
						}
					});
				});
			}
		},

		'unlinkAction': function(leftVal, rightVal) {
			$.ajax({
				type: 'POST',
				url: '/janeway/production-unlink/',
				data: {'demozoo_id': leftVal, 'janeway_id': rightVal},
				beforeSend: function(xhr) {
					/* need to add CSRF token to the request so that Django will accept it */
					xhr.setRequestHeader('X-CSRFToken', $.cookie('csrftoken'));
				}
			});
		},
		'leftListSelector': 'ul.unmatched_demozoo_prods',
		'rightListSelector': 'ul.unmatched_janeway_prods',
		'linkAction': function(leftVal, rightVal) {
			/* post the ID pair to the server */
			$.ajax({
				type: 'POST',
				url: '/janeway/production-link/',
				data: {'demozoo_id': leftVal, 'janeway_id': rightVal},
				beforeSend: function(xhr) {
					/* need to add CSRF token to the request so that Django will accept it */
					xhr.setRequestHeader('X-CSRFToken', $.cookie('csrftoken'));
				}
			});
		}
	});
});
