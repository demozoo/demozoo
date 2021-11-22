import io
import os

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models
from PIL import Image


class ModelWithThumbnails(models.Model):
    class Meta:
        abstract = True
        app_label = 'demoscene'

    @staticmethod
    def generate_thumbnail(original_field, thumbnail_field, size, crop=False):
        # Set our max thumbnail size in a tuple (max width, max height)
        thumb_width, thumb_height = size
        aspect_ratio = float(thumb_width) / float(thumb_height)

        original_field.seek(0)
        # create in-memory file object because Image.open will
        # merrily do a read() once for every format handler it has,
        # which definitely isn't what we want if the underlying file is on S3...
        original_file = io.BytesIO(original_field.read())
        image = Image.open(original_file)

        original_format = image.format
        original_filename = os.path.basename(original_field.name)
        original_filename_root, original_filename_ext = os.path.splitext(original_filename)

        if image.mode not in ('L', 'RGB'):
            image = image.convert('RGB')

        if crop:
            width, height = image.size
            if width > height * aspect_ratio:
                # crop left/right to achieve 4:3 aspect ratio
                cropped_width = height * aspect_ratio
                cropped_height = height
            else:
                # crop top/bottom
                cropped_width = width
                cropped_height = width / aspect_ratio
            image = image.crop(
                (
                    int((width - cropped_width) / 2),
                    int((height - cropped_height) / 2),
                    int(width - (width - cropped_width) / 2),
                    int(height - (height - cropped_height) / 2)
                )
            )
        image.thumbnail(size, Image.ANTIALIAS)

        # save the thumbnail to memory
        temp_handle = io.BytesIO()
        if original_format == 'JPEG':
            image.save(temp_handle, 'jpeg')
            new_filename = original_filename_root + '.jpg'
            new_content_type = 'image/jpeg'
        else:
            image.save(temp_handle, 'png')
            new_filename = original_filename_root + '.png'
            new_content_type = 'image/png'
        temp_handle.seek(0)  # rewind the file
        original_field.seek(0)

        # save to the thumbnail field
        suf = SimpleUploadedFile(
            new_filename,
            temp_handle.read(),
            content_type=new_content_type
        )
        thumbnail_field.save(suf.name, suf, save=False)
