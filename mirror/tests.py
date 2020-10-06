from __future__ import unicode_literals

import datetime
from io import BytesIO
from mock import patch

from django.test import TestCase

from mirror.actions import FileTooBig, fetch_link
from mirror.models import ArchiveMember, Download
from productions.models import Production

class TestActions(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        self.pondlife = Production.objects.get(title='Pondlife')

    def test_fetch_content_length_too_big(self):
        link = self.pondlife.links.create(
            link_class='BaseUrl', parameter='http://example.com/pretend-big-file.txt',
            is_download_link=True
        )
        with self.assertRaises(FileTooBig):
            fetch_link(link)

        self.assertTrue(
            Download.objects.filter(
                parameter='http://example.com/pretend-big-file.txt', error_type='FileTooBig'
            ).exists()
        )

    def test_fetch_actual_length_too_big(self):
        link = self.pondlife.links.create(
            link_class='BaseUrl', parameter='http://example.com/real-big-file.txt',
            is_download_link=True
        )
        with self.assertRaises(FileTooBig):
            fetch_link(link)

        self.assertTrue(
            Download.objects.filter(
                parameter='http://example.com/real-big-file.txt', error_type='FileTooBig'
            ).exists()
        )

    @patch('boto3.Session')
    def test_fetch_from_mirror(self, Session):
        link = self.pondlife.links.create(
            link_class='BaseUrl', parameter='http://example.com/pondlife.txt',
            is_download_link=True
        )
        Download.objects.create(
            link_class='BaseUrl', parameter='http://example.com/pondlife.txt',
            downloaded_at=datetime.datetime(2020, 1, 1, 12, 0, 0),
            mirror_s3_key='1/2/pondlife.123.txt'
        )
        session = Session.return_value
        s3 = session.resource.return_value
        bucket = s3.Bucket.return_value
        def download_fileobj(filename, f):
            f.write(b'hello from pondlife.txt')
        bucket.download_fileobj = download_fileobj

        download_blob = fetch_link(link)
        Session.assert_called_once_with(aws_access_key_id='AWS_K3Y', aws_secret_access_key='AWS_S3CR3T')
        self.assertEqual(download_blob.filename, 'pondlife.123.txt')
        self.assertEqual(download_blob.md5, 'ebceeba7ff0d18701e1952cd3865ef22')
        self.assertEqual(download_blob.sha1, '31a1dd3aa79730732bf32f4c8f1e3e4f9ca1aa50')
        self.assertEqual(download_blob.file_size, 23)

    def test_fetch_duplicate_of_existing_file(self):
        link = self.pondlife.links.create(
            link_class='BaseUrl', parameter='http://example.com/pondlife2.txt',
            is_download_link=True
        )
        pondlife3_download = Download.objects.create(
            link_class='BaseUrl', parameter='http://example.com/pondlife3.txt',
            downloaded_at=datetime.datetime(2020, 1, 1, 12, 0, 0),
            mirror_s3_key='1/2/pondlife.123.txt',
            sha1="8df5211e169bdda53f2a4bad98483bd973c3e801"
        )

        download_blob = fetch_link(link)
        self.assertEqual(download_blob.filename, 'pondlife2.txt')
        self.assertEqual(download_blob.sha1, '8df5211e169bdda53f2a4bad98483bd973c3e801')

        # a new Download record pointing to the same mirror entry as pondlife3 should have been created
        pondlife2_download = Download.objects.get(link_class='BaseUrl', parameter='http://example.com/pondlife2.txt')
        self.assertEqual(pondlife2_download.mirror_s3_key, '1/2/pondlife.123.txt')
        self.assertNotEqual(pondlife2_download.pk, pondlife3_download.pk)

    @patch('boto3.Session')
    def test_upload_to_mirror(self, Session):
        link = self.pondlife.links.create(
            link_class='BaseUrl', parameter='http://example.com/pondlife2.txt',
            is_download_link=True
        )

        session = Session.return_value
        s3 = session.resource.return_value
        bucket = s3.Bucket.return_value

        download_blob = fetch_link(link)
        bucket.put_object.assert_called_once_with(
            Key='8d/f5/211e169bdda5/pondlife2.txt', Body=b"hello from pondlife2.txt"
        )

        Session.assert_called_once()
        self.assertEqual(download_blob.filename, 'pondlife2.txt')
        self.assertEqual(download_blob.file_size, 24)
        download = Download.objects.get(link_class='BaseUrl', parameter='http://example.com/pondlife2.txt')
        self.assertEqual(download.mirror_s3_key, '8d/f5/211e169bdda5/pondlife2.txt')

    @patch('boto3.Session')
    def test_upload_zipfile(self, Session):
        link = self.pondlife.links.create(
            link_class='BaseUrl', parameter='http://example.com/rubber.zip',
            is_download_link=True
        )
        session = Session.return_value
        s3 = session.resource.return_value
        bucket = s3.Bucket.return_value

        download_blob = fetch_link(link)
        bucket.put_object.assert_called_once()
        Session.assert_called_once()

        download = Download.objects.get(link_class='BaseUrl', parameter='http://example.com/rubber.zip')
        archive_members = download.get_archive_members()
        self.assertEqual(archive_members.count(), 2)
        self.assertEqual(archive_members.first().filename, '16Kb-RUBBER.txt')


class TestModels(TestCase):
    def test_archive_member(self):
        am1 = ArchiveMember.objects.create(archive_sha1='12341234', filename='picture.GIF', file_size=1234)
        am2 = ArchiveMember.objects.create(archive_sha1='12341234', filename='readme', file_size=123)
        self.assertEqual(str(am1), 'picture.GIF')
        self.assertEqual(str(am2), 'readme')
        self.assertEqual(am1.file_extension, 'gif')
        self.assertEqual(am2.file_extension, None)
