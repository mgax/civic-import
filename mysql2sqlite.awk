#!/usr/bin/env awk -f

# copied and modified from https://gist.github.com/943776

# Awk is choosen because it's fast and portable. You can use gawk, original awk or even the lightning fast mawk.
# The mysqldump file is traversed only once.

# Converts a mysqldump file into a Sqlite 3 compatible file. It also extracts the MySQL `KEY xxxxx` from the
# CREATE block and create them in separate commands _after_ all the INSERTs.

# Usage:
# $ mysqldump --compatible=ansi --skip-extended-insert --compact $DB_NAME > dump.sql
# $ ./mysql2sqlite.awk < dump.sql | sqlite3 database.sqlite

BEGIN{ FS=",$" }

# Skip comments
/^\/\*/ { next }

## Skip insert
#/^INSERT/ { next }

# Print all `INSERT` lines. The single quotes are protected by another single quote.
/INSERT/ { gsub( /\\\047/, "\047\047" ); print; next }

# Print the ´CREATE´ line as is and capture the table name.
/^CREATE/ {
	print
	if ( match( $0, /\"[^\"]+/ ) ) tableName = substr( $0, RSTART+1, RLENGTH-1 ) 
}

# Replace `FULLTEXT KEY` or any other `XXXXX KEY` except PRIMARY by `KEY`
/^  [^"]+KEY/ && !/^  PRIMARY KEY/ { gsub( /.+KEY/, "  KEY" ) }

# Print all fields definition lines except the `KEY` lines.
/^  / && !/^(  KEY|\);)/ {
	gsub( /AUTO_INCREMENT/, "" )
	gsub( /CHARACTER SET [^ ]+[ ,]/, "" )
	gsub( /DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP/, "" )
	gsub( /COLLATE [^ ]+[ ,]/, "" )
	gsub( /COMMENT ('[^']+')[ ,]/, "" )
#	gsub(/enum[^)]+\)/, "text ")
#	gsub(/set\([^)]+\)/, "text ")
	gsub(/unsigned/, "")
	if (prev) print prev ","
	prev = $1
}

# `KEY` lines are extracted from the `CREATE` block and stored in array for later print 
# in a separate `CREATE KEY` command. The index name is prefixed by the table name to 
# avoid a sqlite error for duplicate index name.
/^(  KEY|\);)/ {
	if (prev) print prev
	prev=""
	if ($0 == ");"){
		print
	} else {
		if ( match( $0, /\"[^\"]+/ ) ) indexName = substr( $0, RSTART+1, RLENGTH-1 ) 
		if ( match( $0, /\([^\)]+/ ) ) indexKey = substr( $0, RSTART+1, RLENGTH-1 ) 
		key[tableName]=key[tableName] "CREATE INDEX \"" tableName "_" indexName "\" ON \"" tableName "\" (" indexKey ");\n"
	}
}

# Print all `KEY` creation lines.
# but we don't need keys
#END {
#	for (table in key) printf key[table]
#}
