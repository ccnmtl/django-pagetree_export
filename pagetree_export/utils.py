from __future__ import unicode_literals

import cgi
from pagetree.models import PageBlock


def asbool(str):
    return str.lower() == "true"


def sanitize(label):
    return cgi.escape(label, True)


def get_all_pageblocks(hierarchy):
    return PageBlock.objects.filter(section__hierarchy=hierarchy)
