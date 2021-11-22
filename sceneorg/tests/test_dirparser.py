import gzip
from io import BytesIO

from django.test import TestCase
from mock import patch

from sceneorg.dirparser import parse_all_dirs


class TestDirParser(TestCase):
    @patch('sceneorg.dirparser.FTP')
    def test_parse_all_dirs(self, FTP):
        ftp = FTP.return_value

        def retrbinary(command, callback):
            f = BytesIO()
            gzfile = gzip.GzipFile(filename='ls-lR', mode='wb', fileobj=f)
            gzfile.write(b"""pub:
total 28
drwxrwsr-x   6 jeffry ftpadm   65 Jan 22  2008 demos
lrwxrwxrwx   1 jeffry ftpadm   10 Aug 19  2006 mirrors -> ../mirrors
-rw-rw-r--   1 jeffry ftpadm 2129 Sep 10 20:46 uploading.txt
""")
            gzfile.close()
            callback(f.getvalue())

        ftp.retrbinary = retrbinary

        dirs = list(parse_all_dirs())
        ftp.login.assert_called_with('anonymous', 'gasman@raww.org')

        root_path, files = dirs[0]
        self.assertEqual(root_path, '/')

        self.assertEqual(files[0], ('demos', True, None))
        self.assertEqual(files[1], ('mirrors', False, None))
        self.assertEqual(files[2], ('uploading.txt', False, '2129'))

    @patch('sceneorg.dirparser.FTP')
    def test_parse_all_dirs_missing_dir_line(self, FTP):
        ftp = FTP.return_value

        def retrbinary(command, callback):
            f = BytesIO()
            gzfile = gzip.GzipFile(filename='ls-lR', mode='wb', fileobj=f)
            gzfile.write(b"""this is not the directory listing you are looking for""")
            gzfile.close()
            callback(f.getvalue())

        ftp.retrbinary = retrbinary

        with self.assertRaises(Exception):
            list(parse_all_dirs())

    @patch('sceneorg.dirparser.FTP')
    def test_parse_all_dirs_missing_total_line(self, FTP):
        ftp = FTP.return_value

        def retrbinary(command, callback):
            f = BytesIO()
            gzfile = gzip.GzipFile(filename='ls-lR', mode='wb', fileobj=f)
            gzfile.write(b"""pub:
a building with beer in, but that's not important right now
""")
            gzfile.close()
            callback(f.getvalue())

        ftp.retrbinary = retrbinary

        with self.assertRaises(Exception):
            list(parse_all_dirs())

    @patch('sceneorg.dirparser.FTP')
    def test_parse_all_dirs_missing_dir_entry(self, FTP):
        ftp = FTP.return_value

        def retrbinary(command, callback):
            f = BytesIO()
            gzfile = gzip.GzipFile(filename='ls-lR', mode='wb', fileobj=f)
            gzfile.write(b"""pub:
total 28
would you like some toast?
""")
            gzfile.close()
            callback(f.getvalue())

        ftp.retrbinary = retrbinary

        with self.assertRaises(Exception):
            list(parse_all_dirs())
