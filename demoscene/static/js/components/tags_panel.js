$(function() {
	$('.tags_panel').each(function() {
		var panel = $(this);

		var addTagForm = panel.find('form.add_tag');
		var tagList = panel.find('ul.tags');

		/* only proceed if we actually have an addTagForm
			(i.e. user is logged in and site is in editable mode) */
		if (!addTagForm.length) return;

		function ajaxifyTagLi(li) {
			$('form', li).submit(function() {
				$.post(this.action, $(this).serialize(), function() {
					$(li).fadeOut('fast', function() {$(this).remove();});
				});
				return false;
			});
		}

		tagList.find('li').each(function() {
			ajaxifyTagLi(this);
		});

		addTagForm.submit(function() {
			$.post(this.action, $(this).serialize(), function(html) {
				var newLi = $(html);
				tagList.append(newLi);
				ajaxifyTagLi(newLi);
			});

			$('input:text', this).val('');

			return false;
		});

	});
});
