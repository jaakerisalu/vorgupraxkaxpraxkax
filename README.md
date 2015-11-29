# README for vorgupraxkaxpraxkax

 - Python:  3.4
 - DB:      PostgreSQL (locally SQLite)

## Setting up development

**Create virtualenv**

 `virtualenv --python=python3.4 --no-site-packages venv`

 `. ./venv/bin/activate`

**Install dependencies**

 `pip install -r requirements/local.txt`

**Switch to internal vorgupraxkaxpraxkax dir**

 `cd vorgupraxkaxpraxkax`

**Create local settings**

Look below if you'd like to use PostgreSQL locally

Create settings/local.py from settings/local.py.example

**Syncdb & migrate**

 `python manage.py makemigrations accounts`

 `python manage.py migrate`
  
 `python manage.py syncdb`
 
Create a superuser to log in to admin
 
**Run development servers**

**Note:** Virtualenv must be activated for the following commands to work

Run django server: `python manage.py runserver`

**Note:** Server will run at 127.0.0.1:8000 (localhost wont work because of CORS)

**Using PostgreSQL locally**

 `sudo apt-get install postgresql`

Now, with the venv active:
 `pip install psycopg2`

 `sudo -u postgres psql postgres`

 `CREATE USER vorgupraxkaxpraxkax WITH PASSWORD 'vorgupraxkaxpraxkax';`

 `CREATE DATABASE vorgupraxkaxpraxkax;`

 `GRANT ALL ON DATABASE vorgupraxkaxpraxkax TO vorgupraxkaxpraxkax;`

Exit with `CTRL+D`

Uncomment the relevant block in local.py

# README for vorgupraxkaxpraxkax