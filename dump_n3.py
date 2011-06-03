import sparql

class NsIRI(sparql.IRI):
    def __getitem__(self, name):
        return type(self)(self.value + name)

class N3Dumper(object):
    def __init__(self, out_stream):
        self._out_stream = out_stream
        self.count = 0

    def write(self, s, p, o):
        self._out_stream.write("%s %s %s .\n" % (s.n3(), p.n3(), o.n3()))
        self.count += 1

    __call__ = write

_next_id = 0
def new_blank_node():
    global _next_id
    _next_id += 1
    return sparql.BlankNode('B%d' % _next_id)

from rdflib.term import _PythonToXSD
_literal_types = [(cls, (cast or unicode, str(datatype_ref)))
                  for (cls, (cast, datatype_ref)) in _PythonToXSD]

def make_literal(value):
    for cls, (cast, datatype) in _literal_types:
        if isinstance(value, cls):
            break

    else:
        cast, datatype = unicode, None

    return sparql.Literal(value, datatype)
