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
    type, export_fn = get_exporter(object.__class__)
    print >> xmlfile, \
        u"""<pageblock id="%s" type="%s" label="%s" ordinality="%s">""" % (
        block.pk, type, sanitize(block.label), block.ordinality)
    export_fn(object, xmlfile, zipfile)
    print >> xmlfile, "</pageblock>"

def export_node(node, xmlfile, zipfile):
    print >> xmlfile, \
        u"""<section slug="%s" label="%s" is_root="%s">""" % (
        node.slug, sanitize(node.label), node.is_root())
    for block in node.pageblock_set.all():
        export_block(block, xmlfile, zipfile)
    for child in node.get_children():
        export_node(child, xmlfile, zipfile)
    print >> xmlfile, "</section>"

def export_zip(hierarchy):
    root = hierarchy.get_root()

    fd, zip_filename = tempfile.mkstemp(prefix="pagetree-export", suffix=".zip")
    zipfile = ZipFile(zip_filename, 'w')
    zipfile.writestr("version.txt", "1")

    fd, xml_filename = tempfile.mkstemp(prefix="pagetree-site", suffix=".xml")
    xmlfile = codecs.open(xml_filename, 'w', encoding='utf8')

    print >> xmlfile, \
        u"""<hierarchy name="%s" base_url="%s">""" % (
        hierarchy.name, hierarchy.base_url)

    export_node(root, xmlfile, zipfile)
    print >> xmlfile, "</hierarchy>"

    xmlfile.close()
    zipfile.write(xml_filename, arcname="site.xml")
    os.unlink(xml_filename)

    zipfile.close()
    return zip_filename

def import_pageblock(hierarchy, section, pageblock, zipfile):
    type = pageblock.get("type")
    label = pageblock.get("label")
    ordinality = pageblock.get("ordinality")

    block = get_importer(type)(pageblock, zipfile)
    pb = PageBlock(section=section, ordinality=ordinality, label=label, content_object=block)
    pb.save()
    return pb

def import_node(hierarchy, section, zipfile, parent=None):
    slug = section.get("slug")
    label = section.get("label")
    is_root = asbool(section.get("is_root"))
    assert (parent and not is_root) or (is_root and not parent)

    if parent is None:
        s = hierarchy.get_root()
        s.slug = slug
        s.label = label
        s.save()
    else:
        s = parent.append_child(label, slug)
        s.save()

    for child in section.iterchildren():
        if child.tag == "pageblock":
            import_pageblock(hierarchy, s, child, zipfile)
        elif child.tag == "section":
            import_node(hierarchy, child, zipfile, parent=s)
        else:
            raise TypeError("Badly formatted import file")

    return s

from pagetree.helpers import get_hierarchy

def import_zip(zipfile, hierarchy_name=None):
    if 'site.xml' not in zipfile.namelist():
        raise TypeError("Badly formatted import file")
    if 'version.txt' not in zipfile.namelist():
        raise TypeError("Badly formatted import file")
    if zipfile.read("version.txt") != "1":
        raise TypeError("Badly formatted import file")
    structure = zipfile.read("site.xml")
    structure = etree.fromstring(structure)

    name = hierarchy_name or structure.get("name")
    base_url = structure.get("base_url")

    hierarchy = get_hierarchy(name=name)
    hierarchy.base_url = base_url
    hierarchy.save()

    for section in structure.iterchildren():
        import_node(hierarchy, section, zipfile)

    return hierarchy
