FROM mcr.microsoft.com/devcontainers/python:1-3.10-bookworm

# build-essential:     pyrecoil publishes no Linux wheels (macOS only), so pip builds
#                      it from its sdist and needs a C toolchain + Python headers.
#                      This is what `python3.10-dev` was doing in etc/vagrant-provision.sh.
# libpq5:              requirements-common.txt pins plain `psycopg` (not psycopg[binary]),
#                      which is a pure-Python wheel that dlopens libpq at runtime.
#                      Arrives as a dependency of postgresql-client.
# postgresql-client:   gives you `psql` for poking at the database.
# redis-tools:         gives you `redis-cli`.
# libffi-dev:          bcrypt, still used by some legacy account password hashes.
# The base image ships a yarn apt source whose signing key has expired, which makes
# `apt-get update` fail. Nothing here needs yarn from apt, so drop the source.
RUN rm -f /etc/apt/sources.list.d/yarn.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
        postgresql-client \
        redis-tools \
    && rm -rf /var/lib/apt/lists/*
