from __future__ import absolute_import, unicode_literals

import os
import uuid


def random_path(prefix, filepath):
    hex = uuid.uuid4().hex
    filename = os.path.basename(filepath)
    filename_root, filename_ext = os.path.splitext(filename)
    return prefix + '/' + hex[0] + '/' + hex[1] + '/' + hex[2:] + filename_ext
