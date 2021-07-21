from __future__ import absolute_import, unicode_literals

import gzip
import io
import re
from ftplib import FTP


def parse_all_dirs():
    ftp = FTP('ftp.scene.org')
    ftp.login('anonymous', 'gasman@raww.org')
    gzipped_file = io.BytesIO()
    ftp.retrbinary('RETR ls-lR.gz', gzipped_file.write)
    ftp.quit()

    gzipped_file.seek(0)
    f = gzip.GzipFile(fileobj=gzipped_file)

    while True:
        # read the ls-lR file as iso-8859-1 - not because it actually IS iso-8859-1
        # (it's actually utf-8), but because we want to preserve the filenames in
        # bytestring form (and iso-8859-1 is the hack we use to store bytestrings in
        # a unicode database field).
        line = f.readline().decode('iso-8859-1')
        if not line:
            break

        m = re.match(r'pub(.*):$', line)
        if m:
            dir_name = m.group(1) + '/'
            # print "found dir: %s" % dir_name
        else:
            raise Exception("Expected dir name line, got %r" % line)

        line = f.readline().decode('iso-8859-1')
        if not re.match(r'total \d+$', line):
            raise Exception("Expected 'total' line, got %r" % line)

        entries = get_dir_listing(f)
        if not dir_name.startswith('/incoming/'):
            yield (dir_name, entries)


def pointless_call_to_make_coverage_notice_this_line():
    pass


def get_dir_listing(f):
    entries = []

    while True:
        line = f.readline().decode('iso-8859-1')
        if not line or line == "\n":
            pointless_call_to_make_coverage_notice_this_line()
            break

        m = re.match(r'(.)[rwsx-]{9}\+? +\d+ +\w+ +\w+ +(\d+) \w{3} +\d+ +\d\d:?\d\d (.*)', line)
        if m:
            node_type, file_size, filename = m.groups(0)
            if node_type == '-':
                entries.append((filename, False, file_size))
            elif node_type == 'l':
                entries.append((filename.split(' ')[0], False, None))
            elif node_type == 'd':
                entries.append((filename, True, None))
        else:
            raise Exception("Expected dir entry, got %r" % line)

    return entries
