from __future__ import absolute_import, unicode_literals

import json

from django.template import Library


register = Library()


def jsonify(object):
    return json.dumps(object)


register.filter('json', jsonify)
