import codecs
from django.core.files import File
import lxml.etree as etree
from pageblocks.models import *
from pagetree.models import *
import tempfile
from zipfile import ZipFile

from pagetree_export import (register_class as register,
                             get_exporter, get_importer)
from pagetree_export.utils import asbool, sanitize, get_all_pageblocks


def export_block(block, xmlfile, zipfile):
    object = block.content_object
    try:
        type, export_fn = get_exporter(object.__class__, export_type='statichtml')
    except KeyError:
        return {}
    return export_fn(object, xmlfile, zipfile)

def export_node(node, xmlfile, zipfile):
    print >> xmlfile, \
        u"""<li><a href="%s">%s</a></li>""" % (
        node.get_absolute_url(), sanitize(node.label))

    if node.pageblock_set.count():
        fd, node_filename = tempfile.mkstemp(prefix="pagetree-site", suffix=".html")
        nodefile = codecs.open(node_filename, 'w', encoding='utf8')
        print >> nodefile, u"<html><head><title>%s</title></head><body>" % node.label

        for block in node.pageblock_set.all():
            data = export_block(block, nodefile, zipfile)
            print >> nodefile, block.render(**data)

        print >> nodefile, u"</body></html>"
        nodefile.close()
        basename = node.get_absolute_url().strip('/')
        if not basename:
            basename = 'index'
        arcname = "pageblocks/" + basename + '.html'
        zipfile.write(node_filename, arcname=arcname)
        os.unlink(node_filename)

    for child in node.get_children():
        print >> xmlfile, u"<ul>"
        export_node(child, xmlfile, zipfile)
        print >> xmlfile, u"</ul>"

def export_zip(hierarchy):
    root = hierarchy.get_root()

    fd, zip_filename = tempfile.mkstemp(prefix="pagetree-export", suffix=".zip")
    zipfile = ZipFile(zip_filename, 'w')
    zipfile.writestr("version.txt", "1")

    fd, xml_filename = tempfile.mkstemp(prefix="pagetree-site", suffix=".html")
    xmlfile = codecs.open(xml_filename, 'w', encoding='utf8')

    print >> xmlfile, \
        u"""<html><head><title>%s</title><base href="%s/pageblocks/" /></head><body><ul>""" % (
        hierarchy.name, hierarchy.base_url.strip('/'))

    export_node(root, xmlfile, zipfile)
    print >> xmlfile, "</ul></body></html>"

    xmlfile.close()
    zipfile.write(xml_filename, arcname="index.html")
    os.unlink(xml_filename)

    zipfile.close()
    return zip_filename
