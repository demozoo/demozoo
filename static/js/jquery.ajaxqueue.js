/*
Ajax queueing implementation, for e.g. text field autocompletion.
Wrap your ajax-firing event handlers in this, and it will ensure that
the handler is only retriggered when the previous ajax call completes
(which should be signalled by calling the release() function passed as
a parameter).

$.ajaxQueue(actionId, function(release) {
	$.get('/example/', function(result) {
		doSomethingWith(result);
		release();
	})
})

TODO: Some kind of mechanism to prevent users from navigating away while
there are still queued ajax events yet to complete
	(just a wrapper for 'is ajaxQueueLocks nonempty?', really...?)
*/

var ajaxQueueLocks = {};
(function($) {
	$.ajaxQueue = function(actionId, callback) {
		function release() {
			var nextCallback = ajaxQueueLocks[actionId].nextCallback;
			delete ajaxQueueLocks[actionId].nextCallback;
			if (nextCallback) {
				/* there is a queued callback to run now; leave locked */
				nextCallback(release);
			} else {
				/* no queued callback; unlock and exit */
				delete ajaxQueueLocks[actionId];
			}
		}
		
		if (ajaxQueueLocks[actionId]) {
			/* currently locked; need to queue up callback */
			ajaxQueueLocks[actionId].nextCallback = callback;
		} else {
			/* not locked; can run callback immediately */
			ajaxQueueLocks[actionId] = {
				locked: true
			}
			callback(release);
		}
	}
})(jQuery);
