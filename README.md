Installation
============

    pip install django-pagetree_export

Usage
=====

This is a library, not an app; so you'll have to integrate it
into your Django project manually.  The interesting functions
are:

    from pagetree_export.exportimport import export_zip
    from pagetree_export.exportimport import import_zip

They do what you'd expect: export a pagetree hierarchy to a zipfile,
and import a zipfile to a pagetree hierarchy.  You can use them in
views like:

    hierarchy = pagetree.helpers.get_hierarchy(name="main")
    filename = export_zip(hierarchy)
    with open(filename) as zipfile:
    	 resp = HttpResponse(zipfile.read())
    resp['Content-Disposition'] = "attachment; filename=pagetree-export.zip"
    os.unlink(filename)
    return resp

Note that `export_zip` returns a _filename_ which can be used to read 
and return the contents of a zipfile.  The file it creates is a
temporary file (i.e. it lives under /tmp) so you don't have to worry
about it too much, but you should remember to be polite and remove the
tempfile from the system before returning the HTTP response.

And here's the corresponding import:

    from zipfile import ZipFile
    file = request.FILES['file']
    zipfile = ZipFile(file)
    new_hierarchy = import_zip(zipfile)

The `import_zip` function takes a `zipfile.ZipFile` which is an object
in the Python standard library.  You can get a ZipFile object from a
Django file upload by wrapping the object, as shown in the sample
above.

Details
-------

When importing a hierarchy from a zipfile, the system prevents
duplicate hierarchies with identical names, and duplicate root nodes
within a hierarchy, by using `get_or_create` rather than `create`.  If
a matching hierarchy (or a root node) already exists, its attributes
will be replaced with the attributes described in the imported
zipfile. You probably don't need to worry about this.

Extensions
==========

You can plug in new exporters and importers for particular types of
pageblocks.

An export function takes a PageBlock, an open writable XML file, and
an open writable zipfile; it should at minimum write to the XML file
at its current position, and may also want to write extra files to the
zipfile.

An import function takes an xml.etree node and an open readable
zipfile; it should at minimum parse the node (and its children) to
generate a new PageBlock, and may also want to read extra files from
the zipfile.  It should return the newly-created PageBlock.

You will need to register your exporter and importer functions like
so:

    from pagetree_export import register
    register(MyPageBlockClass, "mypageblockclass", 
             my_export_fn, my_import_fn)

If you prefer, you can organize your code with classes, and register
the classes with a decorator.  The contract for these classes is:

    from pagetree_export import register_class

    @register_class
    class MyExporter(object):
        block_class = MyPageBlockClass
	identifier = "mypageblockclass"

	def exporter(self, block, xmlfile, zipfile):
	    """ write to the file, return nothing """

	def importer(self, etree_node, zipfile):
            new_block = MyPageBlockClass(**some_attributes)
 	    new_block.save()
	    return new_block

The `exporter` and `importer` methods are both optional; you can omit
one or the other of them to register an exporter with no corresponding
importer, or vice versa.  The `block_class` and `identifier`
attributes are not optional.
