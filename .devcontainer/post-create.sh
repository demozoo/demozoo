#!/usr/bin/env bash
#
# Runs once, after the dev container is created. Mirrors what
# etc/vagrant-provision.sh did inside the Vagrant VM, minus everything docker-compose
# already provides (Python, Postgres, Redis, Node).
set -euo pipefail

cd /workspaces/demozoo

say() { printf '\n\033[1;36m==> %s\033[0m\n' "$1"; }

# ---------------------------------------------------------------------------
# .env
# ---------------------------------------------------------------------------
# Database and Redis settings are injected as real environment variables by
# docker-compose. django-dotenv's read_dotenv() defaults to override=False, i.e. it
# uses os.environ.setdefault, so the compose values win and this file only has to
# carry the things compose does not set.
if [ ! -f .env ]; then
    say "Writing .env"
    SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(64))')"
    cat > .env <<EOM
SECRET_KEY="${SECRET_KEY}"

AWS_STORAGE_BUCKET_NAME="my-demozoo-media"

AWS_ACCESS_KEY_ID="get one from http://aws.amazon.com/s3/"
AWS_SECRET_ACCESS_KEY="get one from http://aws.amazon.com/s3/"

SCENEID_KEY="please read https://id.scene.org/docs/"
SCENEID_SECRET="please read https://id.scene.org/docs/"

# Database and Redis connection settings come from .devcontainer/docker-compose.yml.

# Read-only mode:
# SITE_IS_WRITEABLE=0

# Disable debug toolbar in development:
# DEBUG_TOOLBAR_ENABLED=0
EOM
else
    say ".env already exists, leaving it alone"
fi

# ---------------------------------------------------------------------------
# Python dependencies
# ---------------------------------------------------------------------------
# pyrecoil has no Linux wheels and is compiled here, so this is the slow step.
say "Installing Python dependencies"
python -m pip install --user --upgrade pip
python -m pip install --user -r requirements.txt

# ---------------------------------------------------------------------------
# Front-end assets
# ---------------------------------------------------------------------------
# static_built/css/dz.css and static_built/images/icons.svg are gitignored build
# products. Skipping this leaves the site unstyled and iconless -- it is the gap the
# README calls out as making the Docker setup "experimental".
say "Building front-end assets"
npm ci --no-audit --no-fund
npm run build

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
# First boot restores the full public export, which takes a long time. Later boots
# reuse the pgdata volume and this returns immediately.
say "Waiting for PostgreSQL (first run imports the Demozoo export; expect a long wait)"
until pg_isready -h db -U demozoo -d demozoo -q; do
    printf '.'
    sleep 5
done
printf '\n'

# The schema in git is usually ahead of the published export.
say "Applying migrations"
./manage.py migrate

say "Ready. Start the site with:  ./manage.py runserver 0.0.0.0:8000"
