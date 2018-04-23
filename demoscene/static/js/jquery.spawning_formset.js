(function($) {
	$.fn.spawningFormset = function(opts) {
		if (!opts) opts = {};
		this.each(function() {
			var formset = this;
			var totalFormsInput = $("input[type='hidden'][name$='TOTAL_FORMS']", this);
			var fieldPrefix = totalFormsInput.attr('name').replace(/TOTAL_FORMS$/, '');
			
			function deleteForm(li) {
				$('.delete input:checkbox', li).attr('checked', true);
				//$('> *', li).fadeOut(); /* fading out the LI itself is borked on Webkit (as of 2010-06-01) */
				$(li).fadeOut();
			}
			
			$('> ul > li', this).each(function() {
				var li = this;
				var deleteButton = $('<a href="javascript:void(0);" class="delete_button" title="delete">delete</a>');
				deleteButton.click(function() {
					deleteForm(li);
				});
				/* using display: none screws with fading / ordering in unexplainable ways on Webkit */
				$('.delete', li).css({'font-size': '1px', 'visibility':'hidden'}).after(deleteButton);
			});
			
			var placeholderElement = $('> ul > li.placeholder_form', this);
			var newFormTemplate = placeholderElement.clone();
			newFormTemplate.removeClass('placeholder_form');
			placeholderElement.remove();
			
			if (totalFormsInput.val() > 1 || $(this).hasClass('initially_hidden')) {
				var unboundForm = $('> ul > li:last.unbound', this);
				if (unboundForm.length) {
					unboundForm.remove();
					totalFormsInput.val(totalFormsInput.val() - 1);
				}
			}
			
			var addButtonText = $(formset).data('add-button-text') || 'add';
			var addButton = $('<a href="javascript:void(0);" class="add_button"></a>').text(addButtonText);
			var addLi = $('<li></li>');
			addLi.append(addButton);
			addButton.click(function() {
				var newForm = newFormTemplate.clone();
				addLi.before(newForm);
				var newIndex = parseInt(totalFormsInput.val());
				totalFormsInput.val(newIndex + 1);
				$(":input[name^='" + fieldPrefix + "']", newForm).each(function() {
					this.name = this.name.replace(fieldPrefix + '__prefix__', fieldPrefix + newIndex);
				})
				$(":input[id^='id_" + fieldPrefix + "']", newForm).each(function() {
					this.id = this.id.replace('id_' + fieldPrefix + '__prefix__', 'id_' + fieldPrefix + newIndex);
				})
				$("label[for^='id_" + fieldPrefix + "']", newForm).each(function() {
					this.htmlFor = this.htmlFor.replace('id_' + fieldPrefix + '__prefix__', 'id_' + fieldPrefix + newIndex);
				})
				$('a.delete_button', newForm).click(function() {
					deleteForm(newForm);
				});
				newForm.hide().show();
				if (opts.onShow) opts.onShow(newForm);
				try {$(':input:visible', newForm)[0].focus();}catch(_){}
			})
			$('> ul', this).append(addLi);
		});
	}
})(jQuery);
