#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username demozoo --dbname demozoo <<-EOSQL
    GRANT ALL PRIVILEGES ON DATABASE demozoo TO demozoo;
EOSQL

echo "Importing Demozoo database export" && \
cat /tmp/demozoo-export.sql | psql --username demozoo demozoo
