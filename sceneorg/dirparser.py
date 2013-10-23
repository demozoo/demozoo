import gzip
import re

def parse_all_dirs(filename):
	f = gzip.open(filename, 'rb')

	while True:
		line = f.readline()
		if not line:
			break

		m = re.match(r'(.*):$', line)
		if m:
			dir_name = m.group(1)
			print "found dir: %s" % dir_name
		else:
			raise Exception("Expected dir name line, got %r" % line)

		line = f.readline()
		if not re.match(r'total \d+$', line):
			raise Exception("Expected 'total' line, got %r" % line)

		parse_dir(f)

	f.close()


def parse_dir(f):
	while True:
		line = f.readline()
		if not line or line == "\n":
			return

		m = re.match(r'(.)[rwsx-]{9} +\d+ \w+ +\w+ +(\d+) \w{3} +\d+ +\d\d:?\d\d (.*)', line)
		if m:
			node_type, file_size, filename = m.groups(0)
			if node_type == '-':
				print "found file %r, size %s" % (filename, file_size)
		else:
			raise Exception("Expected dir entry, got %r" % line)
