"""
Github flavoured markdown - ported from
http://github.github.com/github-flavored-markdown/

Usage:

	html_text = markdown(gfm(markdown_text))

(ie, this filter should be run on the markdown-formatted string BEFORE the markdown
filter itself.)

via:
http://gregbrown.co.nz/code/githib-flavoured-markdown-python-implementation/
https://gist.github.com/457617
https://gist.github.com/710689
"""

import re
from hashlib import md5

def gfm(text):
	# Extract pre blocks.
	extractions = {}
	def pre_extraction_callback(matchobj):
		digest = md5(matchobj.group(0)).hexdigest()
		extractions[digest] = matchobj.group(0)
		return "{gfm-extraction-%s}" % digest
	pattern = re.compile(r'<pre>.*?</pre>', re.MULTILINE | re.DOTALL)
	text = re.sub(pattern, pre_extraction_callback, text)

	# Prevent foo_bar_baz from ending up with an italic word in the middle.
	def italic_callback(matchobj):
		s = matchobj.group(0)
		if list(s).count('_') >= 2:
			return s.replace('_', '\_')
		return s
	pattern = re.compile(r'^(?! {4}|\t)\w+(?<!_)_\w+_\w[\w_]*', re.MULTILINE | re.UNICODE)
	text = re.sub(pattern, italic_callback, text)

	# In very clear cases, let newlines become <br /> tags.
	def newline_callback(matchobj):
		if len(matchobj.group(1)) == 1:
			return matchobj.group(0).rstrip() + '  \n'
		else:
			return matchobj.group(0)
	pattern = re.compile(r'^[\w\<][^\n]*(\n+)', re.MULTILINE | re.UNICODE)
	text = re.sub(pattern, newline_callback, text)

	# Insert pre block extractions.
	def pre_insert_callback(matchobj):
		return '\n\n' + extractions[matchobj.group(1)]
	text = re.sub(r'{gfm-extraction-([0-9a-f]{32})\}', pre_insert_callback, text)

	return text


# Test suite.
try:
	from nose.tools import assert_equal
except ImportError:
	def assert_equal(a, b):
		assert a == b, '%r != %r' % (a, b)

def test_single_underscores():
	"""Don't touch single underscores inside words."""
	assert_equal(
		gfm('foo_bar'),
		'foo_bar',
	)

def test_underscores_code_blocks():
	"""Don't touch underscores in code blocks."""
	assert_equal(
		gfm('    foo_bar_baz'),
		'    foo_bar_baz',
	)

def test_underscores_pre_blocks():
	"""Don't touch underscores in pre blocks."""
	assert_equal(
		gfm('<pre>\nfoo_bar_baz\n</pre>'),
		'\n\n<pre>\nfoo_bar_baz\n</pre>',
	)

def test_pre_block_pre_text():
	"""Don't treat pre blocks with pre-text differently."""
	a = '\n\n<pre>\nthis is `a\\_test` and this\\_too\n</pre>'
	b = 'hmm<pre>\nthis is `a\\_test` and this\\_too\n</pre>'
	assert_equal(
		gfm(a)[2:],
		gfm(b)[3:],
	)

def test_two_underscores():
	"""Escape two or more underscores inside words."""
	assert_equal(
		gfm('foo_bar_baz'),
		'foo\\_bar\\_baz',
	)

def test_newlines_simple():
	"""Turn newlines into br tags in simple cases."""
	assert_equal(
		gfm('foo\nbar'),
		'foo  \nbar',
	)

def test_newlines_group():
	"""Convert newlines in all groups."""
	assert_equal(
		gfm('apple\npear\norange\n\nruby\npython\nerlang'),
		'apple  \npear  \norange\n\nruby  \npython  \nerlang',
	)

def test_newlines_long_group():
	"""Convert newlines in even long groups."""
	assert_equal(
		gfm('apple\npear\norange\nbanana\n\nruby\npython\nerlang'),
		'apple  \npear  \norange  \nbanana\n\nruby  \npython  \nerlang',
	)

def test_newlines_list():
	"""Don't convert newlines in lists."""
	assert_equal(
		gfm('# foo\n# bar'),
		'# foo\n# bar',
	)
	assert_equal(
		gfm('* foo\n* bar'),
		'* foo\n* bar',
	)