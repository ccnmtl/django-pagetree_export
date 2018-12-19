from __future__ import unicode_literals, print_function

import os
import codecs
import tempfile
from zipfile import ZipFile

from pagetree_export import get_exporter
from pagetree_export.utils import sanitize


def export_block(block, xmlfile, zipfile):
    object = block.content_object
    try:
        type, export_fn = get_exporter(
            object.__class__, export_type='statichtml')
    except KeyError:
        return {}
    return export_fn(object, xmlfile, zipfile)


def export_node(node, xmlfile, zipfile):
    print('<li><a href="%s">%s</a></li>' % (
        node.get_absolute_url(), sanitize(node.label)), file=xmlfile)

    if node.pageblock_set.count():
        fd, node_filename = tempfile.mkstemp(
            prefix="pagetree-site", suffix=".html")
        nodefile = codecs.open(node_filename, 'w', encoding='utf8')
        print(
            "<html><head><title>%s</title></head><body>" % node.label,
            file=nodefile)

        for block in node.pageblock_set.all():
            data = export_block(block, nodefile, zipfile)
            print(block.render(**data), file=nodefile)

        print("</body></html>", file=nodefile)
        nodefile.close()
        basename = node.get_absolute_url().strip('/')
        if not basename:
            basename = 'index'
        arcname = "pageblocks/" + basename + '.html'
        zipfile.write(node_filename, arcname=arcname)
        os.unlink(node_filename)

    for child in node.get_children():
        print("<ul>", file=xmlfile)
        export_node(child, xmlfile, zipfile)
        print("</ul>", file=xmlfile)


def export_zip(hierarchy):
    root = hierarchy.get_root()

    fd, zip_filename = tempfile.mkstemp(prefix="pagetree-export",
                                        suffix=".zip")
    zipfile = ZipFile(zip_filename, 'w')
    zipfile.writestr("version.txt", "1")

    fd, xml_filename = tempfile.mkstemp(prefix="pagetree-site",
                                        suffix=".html")
    xmlfile = codecs.open(xml_filename, 'w', encoding='utf8')

    print(
        ('<html><head><title>%s</title><base href="%s/pageblocks/" />' +
         '</head><body><ul>') % (
            hierarchy.name, hierarchy.base_url.strip('/')), file=xmlfile)

    export_node(root, xmlfile, zipfile)
    print("</ul></body></html>", file=xmlfile)

    xmlfile.close()
    zipfile.write(xml_filename, arcname="index.html")
    os.unlink(xml_filename)

    zipfile.close()
    return zip_filename
