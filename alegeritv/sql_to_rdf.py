import sys
import json
import rdflib
import re
from unidecode import unidecode

def force_to_unicode(s):
    if type(s) is unicode:
        return s
    try:
        return s.decode('utf-8')
    except:
        return s.decode('latin-1')

_slug_pattern = re.compile(r'\W+', re.UNICODE)
def slugify(s):
    return _slug_pattern.sub('-', str(unidecode(s)).lower())

civic = rdflib.Namespace('http://civic.grep.ro/')
civic_person = rdflib.Namespace(civic + 'person/')
civic_office = rdflib.Namespace(civic + 'office/')
civic_party = rdflib.Namespace(civic + 'party/')
civic_types = rdflib.Namespace(civic + 'rdftypes/')
civic_election = rdflib.Namespace(civic + 'election/')
dc = rdflib.Namespace('http://purl.org/dc/elements/1.1/')
foaf = rdflib.Namespace('http://xmlns.com/foaf/0.1/')
from rdflib.namespace import RDF, RDFS

# 'county' - judet (NUTS-3)
# 'city' - oras, municipiu
# 'sector' - sector
# 'commune' - comuna

# TODO link with NUTS (http://en.wikipedia.org/wiki/Nomenclature_of_Territorial_Units_for_Statistics)
# TODO which to use, campanii_candidati.id_partid_acum or candidati.id_partid?
# TODO s/civic_types/civic_terms/
# TODO what does campanii_candidati.id_alegere point to?

class DatabaseReader(object):
    def __init__(self, **config):
        import MySQLdb
        db = MySQLdb.connect(use_unicode=True, **config)
        self.cursor = db.cursor()

    def column_names(self, table_name):
        self.cursor.execute("DESCRIBE %s" % table_name)
        return [col[0] for col in self.cursor]

    def dump(self, table_name):
        self.cursor.execute("SELECT * FROM %s" % table_name)
        return (row for row in self.cursor)

    def iter_table(self, table_name):
        columns = self.column_names(table_name)
        for row in self.dump(table_name):
            yield dict(zip(columns, row))


def main():
    graph = rdflib.Graph()

    with open(sys.argv[1], 'rb') as f:
        config = json.load(f)
    sql = DatabaseReader(**config)

    parties = {}
    for row in sql.iter_table('partide'):
        party = civic_party[slugify(row['den_scurta'])]
        graph.add((party, RDFS['label'], rdflib.Literal(row['denumire'])))
        graph.add((party, RDF['type'], civic_types['Party']))
        parties[row['id']] = party

    people = {}
    for row in sql.iter_table('candidati'):
        name =  u"%s %s" % (force_to_unicode(row['prenume']).strip(),
                            force_to_unicode(row['nume']).strip())
        person = civic_person[slugify(name)]
        graph.add((person, foaf['name'], rdflib.Literal(name)))
        graph.add((person, RDF['type'], civic_types['Person']))
        people[row['id']] = person
        party = parties.get(row['id_partid'], None)
        if party is not None:
            graph.add((person, civic_types['memberInParty'], party))

    admin_level_map = {
        3: civic['county/'],  # judet
        4: civic['city/'],    # municipiu
        5: civic['sector/'],  # sector
        6: civic['city/'],    # oras
        7: civic['commune/'], # comuna
    }

    circumscriptii = {}
    for row in sql.iter_table('circumscriptii'):
        admin_level = admin_level_map.get(row['id_tip'])
        if admin_level is None:
            continue
        name = force_to_unicode(row['name'])
        s = slugify(name)
        circumscriptie = rdflib.Namespace(admin_level)[s]

        circumscriptii[row['id']] = circumscriptie
        graph.add((circumscriptie, RDFS['label'], rdflib.Literal(name)))

    election_map = {}
    for row in [{'id': 14, 'name': "2008 Local elections, round 1"},
                {'id': 15, 'name': "2008 Local elections, round 2"}]:
        election = civic_election[slugify(row['name'])]
        graph.add((election, RDF['type'], civic_types['Election']))
        graph.add((election, RDFS['label'], rdflib.Literal(row['name'])))
        election_map[row['id']] = election

    for row in sql.iter_table('campanii_candidati'):
        person = people[row['id_candidat']]
        election = election_map[row['id_alegere']]
        campaign = rdflib.BNode()
        graph.add((campaign, RDF['type'], civic_types['Campaign']))
        graph.add((campaign, civic_types['candidate'], person))
        party = parties.get(row['id_partid_acum'], None)
        if party is not None:
            graph.add((campaign, civic_types['party'], party))
        graph.add((campaign, civic_types['election'], election))
        if row['rezultat_procent'] is not None:
            fraction = rdflib.Literal(float(row['rezultat_procent'] / 100))
            graph.add((campaign, civic_types['voteFraction'], fraction))
        win = bool(row['castigator'] == 3)
        graph.add((campaign, civic_types['win'], rdflib.Literal(win)))
        if win:
            circumscriptie = circumscriptii[row['id_circumscriptie']]
            graph.add((person, civic_office['mayor'], circumscriptie))

    print>>sys.stderr, '%d triples' % len(graph)
    graph.serialize(sys.stdout)

if __name__ == '__main__':
    main()
