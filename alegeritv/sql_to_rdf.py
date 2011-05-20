import sys
import json
import sqlite3
import rdflib
import re

def force_to_unicode(s):
    if type(s) is unicode:
        return s
    try:
        return s.decode('utf-8')
    except:
        return s.decode('latin-1')

_slug_pattern = re.compile(r'\W+', re.UNICODE)
def slugify(s):
    return _slug_pattern.sub('-', s.lower())

civic = rdflib.Namespace('http://civic.grep.ro/')
civic_person = rdflib.Namespace(civic + 'person/')
civic_office = rdflib.Namespace(civic + 'office/')
civic_types = rdflib.Namespace(civic + 'rdftypes/')
dc = rdflib.Namespace('http://purl.org/dc/elements/1.1/')
foaf = rdflib.Namespace('http://xmlns.com/foaf/0.1/')
from rdflib.namespace import RDF

# 'county' - judet (NUTS-3)
# 'city' - oras, municipiu
# 'sector' - sector
# 'commune' - comuna
# TODO link with NUTS (http://en.wikipedia.org/wiki/Nomenclature_of_Territorial_Units_for_Statistics)

class DatabaseReader(object):
    def __init__(self, db_path):
        self.connection = sqlite3.connect(db_path)
        self.connection.text_factory = str

    def iter_table(self, table_name):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM %s" % table_name)
        columns = [col[0] for col in cursor.description]
        for row in cursor:
            yield row[0], dict(zip(columns, row))

def main():
    graph = rdflib.Graph()

    sql = DatabaseReader(sys.argv[1])

    candidati = {}
    for id, row in sql.iter_table('candidati'):
        name =  u"%s %s" % (force_to_unicode(row['prenume']).strip(),
                            force_to_unicode(row['nume']).strip())
        person = civic_person[slugify(name)]
        graph.add((person, foaf['name'], rdflib.Literal(name)))
        graph.add((person, RDF['type'], civic_types['Person']))
        candidati[id] = person

    admin_level_map = {
        3: civic['county/'],  # judet
        4: civic['city/'],    # municipiu
        5: civic['sector/'],  # sector
        6: civic['city/'],    # oras
        7: civic['commune/'], # comuna
    }

    circumscriptii = {}
    for id, row in sql.iter_table('circumscriptii'):
        admin_level = admin_level_map.get(row['id_tip'])
        if admin_level is None:
            continue
        name = force_to_unicode(row['name'])
        s = slugify(name)
        circumscriptie = rdflib.Namespace(admin_level)[s]

        circumscriptii[id] = circumscriptie
        graph.add((circumscriptie, dc['name'], rdflib.Literal(name)))

    for id, row in sql.iter_table('campanii_candidati'):
        if row['castigator'] != 3:
            continue
        person = candidati[row['id_candidat']]
        circumscriptie = circumscriptii[row['id_circumscriptie']]
        graph.add((person, civic_office['mayor'], circumscriptie))

    graph.serialize(sys.stdout)

if __name__ == '__main__':
    main()