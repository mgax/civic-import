import sys
import json
import MySQLdb
from miniorm import MiniOrm

def force_to_unicode(s):
    if type(s) is unicode:
        return s
    try:
        return s.decode('utf-8')
    except:
        return s.decode('latin-1')

def main():
    with open(sys.argv[1]) as f:
        config = dict((str(k),v) for k,v in json.load(f).items())

    connection = MySQLdb.connect(**config)
    o = MiniOrm(connection.cursor())
    tip_circumscriptie = dict(o.iter_table('tipuri_circumscriptii'))

    candidati = {}
    for id, row in o.iter_table('candidati'):
        candidati[id] =  u"%s %s" % (force_to_unicode(row['prenume']),
                                     force_to_unicode(row['nume']))

    circumscriptii = {}
    for id, row in o.iter_table('circumscriptii'):
        # 3 - judet
        # 4 - municipiu
        # 5 - sector
        # 6 - oras
        # 7 - comuna
        if row['id_tip'] in [4,5,6,7]:
            tip = u'primarie'
        elif row['id_tip'] in [3]:
            tip = u'judet'
        else:
            continue
        name = force_to_unicode(row['name'])
        circumscriptii[id] = {'tip': tip, 'name': name}

    functionari = []
    for id, row in o.iter_table('campanii_candidati'):
        #if circumscriptii.get(row['id_circumscriptie'], {}).get('name') != 'Bucuresti':
        #    continue
        if row['castigator'] != 3:
            continue
        functionari.append({
            'nume': candidati[row['id_candidat']],
            'institutie': circumscriptii[row['id_circumscriptie']],
        })

    print len(functionari)

if __name__ == '__main__':
    main()
