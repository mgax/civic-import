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

next_id = 0
def new_blank_node():
    global next_id
    next_id += 1
    return sparql.BlankNode('B%d' % next_id)
