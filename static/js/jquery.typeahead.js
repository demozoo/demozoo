/*
	Event handler for use in typeahead autocompletion fields;
	the passed callback will fire whenever the field content is updated by the user,
	passing the new field value and an 'autocomplete' flag which will
	be true if the field content changes in a way that makes it
	appropriate to autocomplete (i.e. they typed a new letter at
	the end of the field)
*/

$.fn.typeahead = function(callback) {
	this.keydown(function(e) {
		var field = this;
		/*
			compare current field contents to new field contents to decide what to do about autocompletion.
			First, get some details about the initial state
		*/
		var oldValue = $(field).val();
		var selectionWasAtEnd = (field.selectionEnd == oldValue.length);
		var unselectedPortion = oldValue.substring(0, field.selectionStart);
		
		/* Now use setTimeout to let the keydown event run its course */
		setTimeout(function() {
			var newValue = $(field).val();
			if (oldValue == newValue) return;
			if (selectionWasAtEnd
				&& field.selectionStart == newValue.length /* no selection now */
				&& newValue.length == unselectedPortion.length + 1 /* new value is one letter longer */
				&& newValue.indexOf(unselectedPortion) == 0 /* old unselected portion is a prefix of new value */
			) {
				/* autocomplete */
				callback.call(this, newValue, true);
			} else {
				/* have made some other change (e.g. deletion, pasting text); do not autocomplete */
				callback.call(this, newValue, false);
			}
		}, 1);
	})
}
