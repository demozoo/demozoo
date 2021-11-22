from io import BytesIO

import PIL.Image
from django.core.files.images import ImageFile
from django.test import TestCase

from platforms.models import Platform


class TestPlatformModel(TestCase):
    def test_create_thumbnail_landscape(self):
        f = BytesIO()
        image = PIL.Image.new('RGBA', (400, 200), 'white')
        image.save(f, 'PNG')
        image_file = ImageFile(f, name='test.png')

        zx = Platform.objects.create(
            name="ZX Spectrum",
            photo=image_file
        )
        self.assertEqual(zx.photo_width, 400)
        self.assertEqual(zx.photo_height, 200)
        self.assertIn('.png', zx.photo.name)
        self.assertIn('.png', zx.thumbnail.name)
        self.assertIn(zx.thumbnail_width, range(130, 140))
        self.assertIn(zx.thumbnail_height, range(80, 100))

    def test_create_thumbnail_portrait(self):
        f = BytesIO()
        image = PIL.Image.new('RGB', (240, 320), 'white')
        image.save(f, 'JPEG')
        image_file = ImageFile(f, name='test.jpg')

        zx = Platform.objects.create(
            name="ZX Spectrum",
            photo=image_file
        )
        self.assertEqual(zx.photo_width, 240)
        self.assertEqual(zx.photo_height, 320)
        self.assertIn('.jpg', zx.photo.name)
        self.assertIn('.jpg', zx.thumbnail.name)
        self.assertIn(zx.thumbnail_width, range(130, 140))
        self.assertIn(zx.thumbnail_height, range(80, 100))
