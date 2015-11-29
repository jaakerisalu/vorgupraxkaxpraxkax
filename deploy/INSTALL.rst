Deploy guide
============

To deploy:

- Checkout source code to /srv/vorgupraxkaxpraxkax
- Create virtualenv 'venv' and install production requirements
- Install yuglify, if you plan to use js/css compression ('npm -g install yuglify' to install globally)

- Create vorgupraxkaxpraxkax/media/ dir and ensure it's writable by server process (usually this means www-data user)
- Create database and user
- Add local settings
- syncdb, migrate, collectstatic

- Copy gunicorn.conf to /etc/init/gunicorn-vorgupraxkaxpraxkax.conf
- Copy nginx.conf to /etc/nginx/sites-enabled/vorgupraxkaxpraxkax.conf
- start the service and reload nginx


Files in this directory:

- gunicorn.conf - upstart script to start the gunicorn server process.
- nginx.conf - Nginx site configuration
