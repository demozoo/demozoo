# Demozoo

## Developer installation

It's possible to run Demozoo a number of different ways, but work has been done to facilitate running it rather smoothly in either Vagrant or Docker.

First, [clone](https://docs.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository) this very repository to a folder on your hard drive:

```bash
git clone https://github.com/demozoo/demozoo.git
cd demozoo
```

### Vagrant

After installing [Vagrant](https://www.vagrantup.com/) and [VirtualBox](https://www.virtualbox.org/), bring up Demozoo as follows:

```bash
vagrant up
```

This will download an Ubuntu Jammy64 image, install dependencies, and fetch the latest public export of the Demozoo database. To start up the site:

```bash
vagrant ssh
# then within the Vagrant VM:
./manage.py runserver 0.0.0.0:8000
```

Alternatively you may need to run :

```bash
python ./manage.py runserver 0.0.0.0:8000
```
    
The site will now be available at http://localhost:8000/.

### Docker

> [!WARNING]
> Installation under Docker is experimental and work in progress.
> Currently front-end assets (CSS and SVG icons) are not built automatically -
> these must be built manually after installation.

After installing [Docker Desktop](https://www.docker.com/products/docker-desktop), you can bring up Demozoo by typing the following:

```bash
cp .docker/.env.example .docker/.env
docker-compose up
```

This will download the [`postgres:14-bullseye`](https://hub.docker.com/layers/library/postgres/14-bullseye/images/sha256-95c6dbe36bbe193c1eedcbed98a643cc5b92295a20f4c768d1335ecab39114d8?context=explore) and [`python:3.10`](https://hub.docker.com/layers/library/python/3.10/images/sha256-1c26c25390307b64e8ff73e7edf34b4fbeac59d41da41c08da28dc316a721899?context=explore) images and bootstrap the database with data from the latest Demozoo export.

Booting up the first time will take quite a while, as the database import is large, so be patient. The error messages logged from `demozoo-web` during the import can be ignored. When the import is done, `Running the server on http://localhost:8000` should be printed to the console. You should then be able to visit `http://localhost:8000` in a web browser of your choice.

The data files from Postgres are by default stored in the `.docker/db/pgdata` directory. If you want to wipe the database clean, simply delete that folder.

## Rebuilding indices for the database

If you want to work with the search feature, you have to rebuild your database indices first:

```bash
./manage.py reindex
```

This will take a *long* time, but you only need to do it once.

## Creating an admin user

All account passwords in the public database export are blanked, so you'll need to create a new account to log in. To create a superuser account:

```shell
./manage.py createsuperuser
```

and enter the account details when prompted.

## Batteries not included

The procedure above gives you a basic working Demozoo installation, but several features are unavailable due to needing additional configuration:

* file uploads (Amazon S3)
* screenshot processing
* background tasks (scene.org spidering, fetching screenshots from graphics releases...)

Instructions for these will be forthcoming, at least when someone asks for them :-)

Gasman <matt@west.co.tt> - https://twitter.com/gasmanic
