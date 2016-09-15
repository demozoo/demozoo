Demozoo
=======

developer installation
----------------------

The recommended way to set up a developer instance is through [Vagrant](https://www.vagrantup.com/). After installing Vagrant and VirtualBox, install as follows:

    git clone https://github.com/demozoo/demozoo.git
    cd demozoo
    vagrant up

This will download an Ubuntu Trusty64 image, install dependencies, and fetch the latest public export of the Demozoo database. To connect to the site:

```vagrant ssh```

you should see a welcome like this:    
```
Welcome to Ubuntu 14.04.4 LTS (GNU/Linux 3.13.0-85-generic x86_64)

 * Documentation:  https://help.ubuntu.com/

  System information as of Wed Sep 14 12:39:35 UTC 2016

  ...........
(demozoo) vagrant@vagrant-ubuntu-trusty-64:~/demozoo$

```
Then to start DemoZoo from within the Vagrant VM:

```./manage.py runserver 0.0.0.0:8000```
or 
```python ./manage.py runserver 0.0.0.0:8000```
which will result in
```
Validating models...

0 errors found
September 14, 2016 - 13:54:31
Django version 1.6.8, using settings 'settings'
Starting development server at http://0.0.0.0:8000/
Quit the server with CONTROL-C.
```


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
