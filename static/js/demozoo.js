$(function() {
	$('.spawning_formset').each(function() {
		var formset = this;
		var totalFormsInput = $("input[type='hidden'][name$='TOTAL_FORMS']", this);
		var fieldPrefix = totalFormsInput.attr('name').replace(/TOTAL_FORMS$/, '');
		
		function deleteForm(li) {
			$('.delete input:checkbox', li).attr('checked', true);
			$('> *', li).fadeOut(); /* fading out the LI itself is borked on Webkit (as of 2010-06-01) */
		}
		
		$('> ul > li', this).each(function() {
			var li = this;
			var deleteButton = $('<a href="javascript:void(0);" class="delete_button" title="delete">delete</a>');
			deleteButton.click(function() {
				deleteForm(li);
			});
			$('.delete', li).hide().after(deleteButton);
		});
		var lastElement = $('> ul > li:last', this);
		var newFormTemplate = lastElement.clone();
		var newFormInitialIndex = totalFormsInput.val() - 1;
		
		if (totalFormsInput.val() > 1) {
			lastElement.remove();
			totalFormsInput.val(totalFormsInput.val() - 1);
		}
		
		var addButton = $('<a href="javascript:void(0);" class="add_button">add</a>');
		var addLi = $('<li></li>');
		addLi.append(addButton);
		addButton.click(function() {
			var newForm = newFormTemplate.clone();
			addLi.before(newForm);
			var newIndex = parseInt(totalFormsInput.val());
			totalFormsInput.val(newIndex + 1);
			$(":input[name^='" + fieldPrefix + "']", newForm).each(function() {
				this.name = this.name.replace(fieldPrefix + newFormInitialIndex, fieldPrefix + newIndex);
			})
			$(":input[id^='id_" + fieldPrefix + "']", newForm).each(function() {
				this.id = this.id.replace('id_' + fieldPrefix + newFormInitialIndex, 'id_' + fieldPrefix + newIndex);
			})
			$("label[for^='id_" + fieldPrefix + "']", newForm).each(function() {
				this.htmlFor = this.htmlFor.replace('id_' + fieldPrefix + newFormInitialIndex, 'id_' + fieldPrefix + newIndex);
			})
			$('a.delete_button', newForm).click(function() {
				deleteForm(newForm);
			});
			newForm.hide().slideDown('fast');
			$(":input", newForm).focus();
		})
		$('> ul', this).append(addLi);
	})
})
