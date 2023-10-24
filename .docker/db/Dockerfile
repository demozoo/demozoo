FROM postgres:14.0 as build

RUN apt-get update && \
    apt-get install -y --no-install-recommends wget gzip && \
    rm -rf /var/lib/apt/lists/*

# Fetch and extract database export
RUN wget http://data.demozoo.org/demozoo-export.sql.gz -O /tmp/demozoo-export.sql.gz && \
    gunzip -f /tmp/demozoo-export.sql.gz 

FROM postgres:14.0

COPY --from=build /tmp/demozoo-export.sql /tmp/demozoo-export.sql
