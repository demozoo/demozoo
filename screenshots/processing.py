import re

from django.core.files.storage import DefaultStorage


def get_thumbnail_sizing_params(original_size, target_size):
    """
    Given the dimensions of a source image, return a (crop_params, resize_params) tuple that
    specifies how the image should be cropped and resized to generate a thumbnail to fit
    within target_size.
    crop_params = (left, upper, right, lower) or None for no cropping
    resize_params = (width, height) or None for no resizing

    The rules applied are:
    * all resize operations preserve aspect ratio
    * an image smaller than target_size is left unchanged
    * an image with an aspect ratio more than twice as wide as target_size is resized to half
        the target height (or left at original size if it's already this short or shorter), and
        cropped centrally to fit target width.
    * an image with an aspect ratio between 1 and 2 times as wide as target_size is resized to
        fit target width
    * an image with an aspect ratio between 1 and 3 times as tall as target_size is resized to
        fit target height
    * an image with an aspect ratio more than three times as tall as target_size is resized to
        one third of the target width (or left at original size if it's already this narrow or
        narrower), and cropped to the top to fit target height.
    """
    orig_width, orig_height = original_size
    target_width, target_height = target_size

    if orig_width <= target_width and orig_height <= target_height:
        # image is smaller than target size - do not crop or resize
        return (None, None)

    orig_aspect_ratio = float(orig_width) / orig_height
    target_aspect_ratio = float(target_width) / target_height

    if orig_aspect_ratio > 2 * target_aspect_ratio:
        # image with an aspect ratio more than twice as wide as target_size
        final_width = target_width
        final_height = min(orig_height, int(target_height / 2))
        scale_factor = float(final_height) / orig_height

        # scale up final_width to find out what we should crop to
        crop_width = final_width / scale_factor
        crop_margin = int((orig_width - crop_width) / 2)
        crop_params = (crop_margin, 0, crop_margin + int(crop_width), orig_height)
        if final_height == orig_height:
            resize_params = None
        else:
            resize_params = (final_width, final_height)
        return (crop_params, resize_params)
    elif orig_aspect_ratio >= target_aspect_ratio:
        # image with aspect ratio equal or wider to target_size
        final_width = target_width
        scale_factor = float(final_width) / orig_width
        final_height = int(orig_height * scale_factor)
        resize_params = (final_width, final_height)
        return (None, resize_params)
    elif orig_aspect_ratio >= target_aspect_ratio / 3:
        # image with taller aspect ratio than target_size, but not more than 3 times taller
        # (so no need to crop)
        final_height = target_height
        scale_factor = float(final_height) / orig_height
        final_width = int(orig_width * scale_factor)
        resize_params = (final_width, final_height)
        return (None, resize_params)
    else:
        # image with an aspect ratio more than 3 times taller than target_size
        final_height = target_height
        final_width = min(orig_width, int(target_width / 3))
        scale_factor = float(final_width) / orig_width

        # scale up final_height to find out what we should crop to:
        crop_height = final_height / scale_factor
        crop_params = (0, 0, orig_width, int(crop_height))
        if final_width == orig_width:
            resize_params = None
        else:
            resize_params = (final_width, final_height)
        return (crop_params, resize_params)


def upload_to_s3(fp, key_name):
    """
    Upload the contents of file handle 'fp' to the S3 bucket specified by AWS_STORAGE_BUCKET_NAME,
    under the given filename. Return the public URL.
    """
    storage = DefaultStorage()
    saved_name = storage.save(key_name, fp)
    return storage.url(saved_name)


# successively more aggressive rules for what files we should ignore in an archive
# when looking for screenshots - break out as soon as we have exactly one file remaining
IGNORED_ARCHIVE_MEMBER_RULES = [
    re.compile(r"(__MACOSX.*|thumbs.db|.*\/thumbs.db|scene\.org|.*\.txt|.*\.nfo|.*\.diz)$", re.I),
    re.compile(
        r"(__MACOSX.*|thumbs.db|.*\/thumbs.db|scene\.org|.*\.txt|.*\.nfo|.*\.diz|.*stage\s*\d+\.\w+|.*steps?\s*\d+\.\w+|.*wip\s*\d+\.\w+)$",
        re.I,
    ),  # noqa
    re.compile(
        r"(__MACOSX.*|thumbs.db|.*\/thumbs.db|scene\.org|.*\.txt|.*\.nfo|.*\.diz|.*stage\s*\d+\.\w+|.*steps?\s*\d+\.\w+|.*wip\s*\d+\.\w+|.*vaihe\s*\d+\.\w+|.*phase\s*\d+\.\w+)$",
        re.I,
    ),  # noqa
    re.compile(
        r"(__MACOSX.*|thumbs.db|.*\/thumbs.db|scene\.org|.*\.txt|.*\.nfo|.*\.diz|.*stage\s*\d+\.\w+|.*steps?\s*\d+\.\w+|.*wip\s*\d+\.\w+|.*vaihe\s*\d+\.\w+|.*phase\s*\d+\.\w+|.*unsigned\.\w+|.*nosig\.\w+)$",
        re.I,
    ),  # noqa
    re.compile(
        r"(__MACOSX.*|thumbs.db|.*\/thumbs.db|scene\.org|.*\.txt|.*\.nfo|.*\.diz|.*stage.*|.*step.*|.*wip.*|.*vaihe.*|.*phase.*|.*unsigned.*|.*nosig.*|.*wire.*|.*malla.*|.*preview.*|.*work.*)$",
        re.I,
    ),  # noqa
]


def select_screenshot_file(archive_members):
    from screenshots.models import IMAGE_FILE_EXTENSIONS

    # Given a queryset of ArchiveMember objects for a graphic prod, try to determine the one that's
    # most likely to be the final image file to make a screenshot out of. Return its filename, or
    # None if unsuccessful
    for rule in IGNORED_ARCHIVE_MEMBER_RULES:
        interesting_files = []
        for member in archive_members:
            if member.file_size and not rule.match(member.filename):
                interesting_files.append(member)

        if len(interesting_files) == 1:
            break

    if len(interesting_files) == 1:
        if interesting_files[0].file_extension in IMAGE_FILE_EXTENSIONS:
            return interesting_files[0].filename

    return None
