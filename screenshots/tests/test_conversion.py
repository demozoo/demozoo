from __future__ import absolute_import, unicode_literals

import math
import os.path

from django.conf import settings
from django.test import TestCase
from PIL import Image, ImageChops

from screenshots.models import PILConvertibleImage

TEST_IMAGES_DIR = os.path.join(os.path.join(settings.FILEROOT, 'screenshots', 'tests', 'images'))


class TestConversion(TestCase):
    def assertImagesSimilar(self, img1, img2):
        image1 = Image.open(img1)
        image2 = Image.open(img2)
        diff = ImageChops.difference(image1, image2).histogram()

        sq = (value * (i % 256) ** 2 for i, value in enumerate(diff))
        sum_squares = sum(sq)
        result = math.sqrt(sum_squares / float(image1.size[0] * image1.size[1]))

        self.assertTrue(result < 1, "Images are too different")

    def test_wmf(self):
        # WMF is not in our PIL_READABLE_FORMATS list
        with open(os.path.join(TEST_IMAGES_DIR, 'clock.wmf'), mode='rb') as f:
            with self.assertRaises(IOError):
                img = PILConvertibleImage(f, name_hint='clock.wmf')

    def test_gif_palette(self):
        # https://github.com/python-pillow/Pillow/issues/513
        with open(os.path.join(TEST_IMAGES_DIR, 'atari-metal-knight.gif'), mode='rb') as f:
            img = PILConvertibleImage(f, name_hint='atari-metal-knight.gif')
            output, size, format = img.create_thumbnail((200, 150))

        #with open(os.path.join(TEST_IMAGES_DIR, 'atari-metal-knight.out.%s' % format), mode='wb') as f:
        #    f.write(output.getvalue())

        self.assertEqual(size, (200, 125))
        self.assertEqual(format, 'png')
        self.assertImagesSimilar(output, os.path.join(TEST_IMAGES_DIR, 'atari-metal-knight.out.png'))

    def test_rgba_png(self):
        with open(os.path.join(TEST_IMAGES_DIR, 'twintris.png'), mode='rb') as f:
            img = PILConvertibleImage(f, name_hint='twintris.png')
            output, size, format = img.create_thumbnail((200, 150))

        # with open(os.path.join(TEST_IMAGES_DIR, 'twintris.out.%s' % format), mode='wb') as f:
        #     f.write(output.getvalue())

        self.assertEqual(size, (198, 150))
        self.assertEqual(format, 'jpg')
        self.assertImagesSimilar(output, os.path.join(TEST_IMAGES_DIR, 'twintris.out.jpg'))

    def test_lbm(self):
        with open(os.path.join(TEST_IMAGES_DIR, 'doubtcow.lbm'), mode='rb') as f:
            img = PILConvertibleImage(f, name_hint='doubtcow.lbm')
            output, size, format = img.create_thumbnail((200, 150))

        # with open(os.path.join(TEST_IMAGES_DIR, 'doubtcow.out.%s' % format), mode='wb') as f:
        #     f.write(output.getvalue())

        self.assertEqual(size, (200, 125))
        self.assertEqual(format, 'png')
        self.assertImagesSimilar(output, os.path.join(TEST_IMAGES_DIR, 'doubtcow.out.png'))

    def test_scr(self):
        with open(os.path.join(TEST_IMAGES_DIR, 'mr-scene.scr'), mode='rb') as f:
            img = PILConvertibleImage(f, name_hint='mr-scene.scr')
            output, size, format = img.create_thumbnail((200, 150))

        # with open(os.path.join(TEST_IMAGES_DIR, 'mr-scene.out.%s' % format), mode='wb') as f:
        #     f.write(output.getvalue())

        self.assertEqual(size, (200, 150))
        self.assertEqual(format, 'png')
        self.assertImagesSimilar(output, os.path.join(TEST_IMAGES_DIR, 'mr-scene.out.png'))
