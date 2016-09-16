Demozoo
=======

developer installation
----------------------

The recommended way to set up a developer instance is through [Vagrant](https://www.vagrantup.com/). After installing Vagrant and VirtualBox, install as follows:

    git clone https://github.com/demozoo/demozoo.git
    cd demozoo
    vagrant up

This will download an Ubuntu Trusty64 image, install dependencies, and fetch the latest public export of the Demozoo database. To start up the site:

    vagrant ssh
    # then within the Vagrant VM:
    ./manage.py runserver 0.0.0.0:8000

Alternatively you may need to run :
    python ./manage.py runserver 0.0.0.0:8000
    
The site will now be available at http://localhost:8000/.

Rebuilding indices for the database
-----------------------------------

If you want to work with the search feature, you have to rebuild your database indices first:

    ./manage.py index --rebuild --verbose

This will take a *long* time, but you only need to do it once.

Creating an admin user
----------------------

All account passwords in the public database export are blanked, so you'll need to create a new account to log in. To create a superuser account:

    ./manage.py createsuperuser

and enter the account details when prompted.

Batteries not included
----------------------

The procedure above gives you a basic working Demozoo installation, but several features are unavailable due to needing additional configuration:

* file uploads (Amazon S3)
* screenshot processing
* background tasks (scene.org spidering, fetching screenshots from graphics releases...)

Instructions for these will be forthcoming, at least when someone asks for them :-)

Gasman <matt@west.co.tt> - https://twitter.com/gasmanic
