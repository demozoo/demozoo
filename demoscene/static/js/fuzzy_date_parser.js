(function() {
	var monthsByName = {
		'jan': 0, 'january': 0,
		'feb': 1, 'february': 1,
		'mar': 2, 'march': 2,
		'apr': 3, 'april': 3,
		'may': 4,
		'jun': 5, 'june': 5,
		'jul': 6, 'july': 6,
		'aug': 7, 'august': 7,
		'sep': 8, 'sept': 8, 'september': 8,
		'oct': 9, 'october': 9,
		'nov': 10, 'november': 10,
		'dec': 11, 'december': 11
	}
	var recognisedMonthNames = [];
	for (name in monthsByName) recognisedMonthNames.push(name);
	var monthName = '(' + recognisedMonthNames.join('|') + ')';
	var start = '^\\s*';
	var end = '\\s*$';
	var sep = '[\\s\\-\\/\\\\\\.]+';
	var year = '(\\d{4})';
	var num = '(\\d+)';
	
	var regexps = [
		new RegExp(start + year + sep + num + sep + num + end), /* 2010-01-01 */
		new RegExp(start + year + sep + num + end), /* 2010-01 */
		new RegExp(start + year + end), /* 2010 */
		new RegExp(start + num + sep + num + sep + num + end), /* 01/01/2010 */
		new RegExp(start + num + sep + num + end), /* 01/2010 */
		new RegExp(start + num + sep + monthName + sep + num + end, 'i'), /* 1 Jan 2010 */
		new RegExp(start + monthName + sep + num + end, 'i'), /* Jan 2010 */
		new RegExp(start + num + sep + monthName + end, 'i'), /* 1 Jan */
		new RegExp(start + monthName + end, 'i') /* January */
	]
	
	window.parseFuzzyDate = function(str) {
		if (!str) return null;
		var m;
		if (m = str.match(regexps[0])) {
			return new Date(parseInt(m[1], 10), parseInt(m[2], 10)-1, parseInt(m[3], 10));
		} else if (m = str.match(regexps[1])) {
			return new Date(parseInt(m[1], 10), parseInt(m[2], 10)-1, 1);
		} else if (m = str.match(regexps[2])) {
			return new Date(parseInt(m[1], 10), 0, 1);
		} else if (m = str.match(regexps[3])) {
			return new Date(parseInt(m[3], 10), parseInt(m[2], 10)-1, parseInt(m[1], 10));
		} else if (m = str.match(regexps[4])) {
			return new Date(parseInt(m[2], 10), parseInt(m[1], 10)-1, 1);
		} else if (m = str.match(regexps[5])) {
			return new Date(parseInt(m[3], 10), monthsByName[m[2].toLowerCase()], parseInt(m[1], 10));
		} else if (m = str.match(regexps[6])) {
			return new Date(parseInt(m[2], 10), monthsByName[m[1].toLowerCase()], 1);
		} else if (m = str.match(regexps[7])) {
			thisYear = (new Date()).getFullYear();
			return new Date(thisYear, monthsByName[m[2].toLowerCase()], parseInt(m[1], 10));
		} else if (m = str.match(regexps[8])) {
			thisYear = (new Date()).getFullYear();
			return new Date(thisYear, monthsByName[m[1].toLowerCase()], 1);
		} else {
			throw 'Invalid date';
		}
	}

	window.parseStrictDate = function(str) {
		if (!str) return null;
		var m;
		if (m = str.match(regexps[0])) {
			return new Date(parseInt(m[1], 10), parseInt(m[2], 10)-1, parseInt(m[3], 10));
		} else if (m = str.match(regexps[3])) {
			return new Date(parseInt(m[3], 10), parseInt(m[2], 10)-1, parseInt(m[1], 10));
		} else if (m = str.match(regexps[5])) {
			return new Date(parseInt(m[3], 10), monthsByName[m[2].toLowerCase()], parseInt(m[1], 10));
		} else if (m = str.match(regexps[7])) {
			thisYear = (new Date()).getFullYear();
			return new Date(thisYear, monthsByName[m[2].toLowerCase()], parseInt(m[1], 10));
		} else {
			throw 'Invalid date';
		}
	}
})();
