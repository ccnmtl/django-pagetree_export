_pageblock_exporters = {}
_pageblock_importers = {}

def register(block_class, identifier,
             export_fn=None, import_fn=None,
             override=False):
    if not override:
        if export_fn and block_class in _pageblock_exporters:
            raise RuntimeError("A pageblock exporter is already registered "
                               "for class %s" % block_class)
        if import_fn and identifier in _pageblock_importers:
            raise RuntimeError("A pageblock importer is already registered "
                               "for type %s" % identifier)
    if export_fn:
        _pageblock_exporters[block_class] = (identifier, export_fn)
    if import_fn:
        _pageblock_importers[identifier] = import_fn

def register_class(cls):
    block_class = cls.block_class
    identifier = cls.identifier
    inst = cls()
    export_fn = getattr(inst, 'exporter', None)
    import_fn = getattr(inst, 'importer', None)
    register(block_class, identifier, export_fn, import_fn, override=False)
    return cls

def get_exporter(block_class):
    return _pageblock_exporters[block_class]

def get_importer(identifier):
    return _pageblock_importers[identifier]
