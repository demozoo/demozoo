#!/usr/bin/env python

import argparse
import os
import sys
import warnings

from django.core.management import execute_from_command_line


os.environ['DJANGO_SETTINGS_MODULE'] = 'demozoo.settings.test'


def make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--deprecation', choices=['all', 'imminent', 'none'], default='imminent')
    return parser


def parse_args(args=None):
    return make_parser().parse_known_args(args)


def runtests():
    args, rest = parse_args()
    if args.deprecation == 'all':
        # Show all deprecation warnings
        warnings.simplefilter('default', DeprecationWarning)
        warnings.simplefilter('default', PendingDeprecationWarning)
    elif args.deprecation == 'imminent':
        # Show only imminent deprecation warnings
        warnings.filterwarnings('default', category=DeprecationWarning)
    else:
        # Deprecation warnings are ignored by default
        pass

    execute_from_command_line([sys.argv[0], 'test'] + rest)


if __name__ == '__main__':
    runtests()
