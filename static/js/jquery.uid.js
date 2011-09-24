/* generate an ID string (with optional prefix) unique within this page's execution */
var nextUid = 0;
$.uid = function(prefix) {
	return (prefix || '') + (nextUid++);
}
