class MiniOrm(object):
    def __init__(self, cursor):
        self.cursor = cursor

    def column_names(self, table_name):
        self.cursor.execute("DESCRIBE %s" % table_name)
        return [col[0] for col in self.cursor]

    def primary_key(self, table_name):
        self.cursor.execute("DESCRIBE %s" % table_name)
        for col in self.cursor:
            if col[3] == 'PRI':
                return col[0]
        else:
            raise ValueError("No primary key found!")

    def dump(self, table_name):
        self.cursor.execute("SELECT * FROM %s" % table_name)
        return (row for row in self.cursor)

    def iter_table(self, table_name):
        columns = self.column_names(table_name)
        key_idx = columns.index(self.primary_key(table_name))
        for row in self.dump(table_name):
            yield row[key_idx], dict(zip(columns, row))

    def query(self, query):
        self.cursor.execute(query)
        return list(self.cursor)

    def insert(self, table_name, row_data):
        row_cols, row_values = zip(*row_data.items())
        query = ("INSERT INTO %(table)s (%(cols)s) VALUES (%(vals)s)" % {
                    'table': table_name,
                    'cols': ','.join('`%s`' % c for c in row_cols),
                    'vals': ','.join(['%s'] * len(row_values))})
        #log.debug("query %r with values %r", query, row_values)
        self.cursor.execute(query, row_values)
        return self.cursor.lastrowid
