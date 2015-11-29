import re
from StringIO import StringIO
import string
import os

from fabric import colors
from fabric.api import *
from fabric.contrib.console import confirm
from fabric.utils import indent

from django.utils.crypto import get_random_string


"""
    Usage:
        fab TARGET actions

    Actions:
        simple_deploy # Deploy updates without migrations.
            :arg id Identifier to pass to vcs update command.
            :arg silent If true doesn't show confirms.

        offline_deploy # Deploy updates with migrations with server restart.
            :arg id Identifier to pass to vcs update command.
            :arg silent If true doesn't show confirms.

        online_deploy # Deploy updates with migrations without server restart.
            :arg id Identifier to pass to vcs update command.
            :arg silent If true doesn't show confirms.

        version # Get the version deployed to target.
        update_requirements # Perform pip install -r requirements/production.txt

        stop_server # Stop the remote server service.
        start_server # Start the remote server service.
        restart_server # Restart the remote server service.

        migrate_diff # Get the status of migrations needed when upgrading target to the specified version.
            :arg id Identifier of revision to check against.
"""


PRODUCTION_LOCAL_SETTINGS = """from settings.production import *

SECRET_KEY = '${secret_key}'

DATABASES = {
    'default': {
        'ENGINE':'django.db.backends.postgresql_psycopg2',
        'NAME': 'vorgupraxkaxpraxkax',
        'USER': 'vorgupraxkaxpraxkax',
        'PASSWORD': '${db_password}',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}
"""


""" TARGETS """


# Use  .ssh/config  so that you can use hosts defined there.
env.use_ssh_config = True


def defaults():
    env.venv_name = 'venv'
    env.confirm_required = True
    env.code_dir = '/'
    env.vcs_extra = ''
    env.nginx_conf = 'nginx.conf'


@task
def live():
    defaults()
    env.hosts = ['tg-dev']
    env.tag = 'vorgupraxkaxpraxkax-live'
    env.service_name = "gunicorn-vorgupraxkaxpraxkax"

    env.code_dir = '/srv/vorgupraxkaxpraxkax'


""" FUNCTIONS """


@task
def show_log(commit_id=None):
    """ List revisions to apply/unapply when updating to given revision.
        When no revision is given, it default to the head of current branch.
        Returns False when there is nothing to apply/unapply. otherwise revset of revisions that will be applied or
        unapplied (this can be passed to `hg|git status` to see which files changed for example).
    """
    result = vcs_log(commit_id)

    if 'message' in result:
        print(result['message'])
        return False

    elif 'forwards' in result:
        print("Revisions to apply:")
        print(indent(result['forwards']))

    elif 'backwards' in result:
        print("Revisions to rollback:")
        print(indent(result['backwards']))

    return result['revset']


@task
def migrate_diff(id=None, revset=None, silent=False):
    """ Check for migrations needed when updating to the given revision. """
    require('code_dir')

    # Exactly one of id and revset must be given
    assert id or revset
    assert not (id and revset)
    if not revset:
        revset = '.%s%s' % ('::' if get_repo_type() == 'hg' else '.', id)

    migrations = changed_files(revset, "\/(?P<model>\w+)\/migrations\/(?P<migration>.+)")

    if not silent and migrations:
        print "Found %d migrations." % len(migrations)
        print indent(migrations)

    return migrations


@task
def update_requirements(reqs_type='production'):
    """ Install the required packages from the requirements file using pip """
    require('hosts')
    require('code_dir')

    with cd(env.code_dir), prefix('. venv/bin/activate'):
        sudo('pip install -r requirements/%s.txt' % reqs_type)


def migrate(silent=False):
    """ Preform migrations on the database. """

    if not silent:
        request_confirm("migrate")

    management_cmd("migrate --noinput")


@task
def version():
    """ Get current target version hash. """
    require('hosts')
    require('code_dir')
    require('tag')

    print "Target %s version: %s" % (env.tag, colors.yellow(get_version()))


@task
def deploy(id=None, silent=False):
    """ Perform an automatic deploy to the target requested. """
    require('hosts')
    require('code_dir')

    # Ask for sudo at the begginning so we don't fail during deployment because of wrong pass
    if not sudo('whoami'):
        abort('Failed to elevate to root')
        return

    # Show log of changes, return if nothing to do
    revset = show_log(id)
    if not revset:
        return

    # See if we have any requirements changes
    requirements_changes = changed_files(revset, r' requirements/')
    if requirements_changes:
        print colors.yellow("Will update requirements (and do migrations):")
        print indent(requirements_changes)

    # See if we have any changes to migrations between the revisions we're applying
    migrations = migrate_diff(revset=revset, silent=True)
    if migrations:
        print colors.yellow("Will apply %d migrations:" % len(migrations))
        print indent(migrations)

    # see if nginx conf has changed
    if changed_files(revset, r' deploy/%s' % env.nginx_conf):
        print colors.red("Warning: Nginx configuration change detected, also run: `fab %target% nginx_update`")

    if not silent:
        request_confirm("deploy")

    vcs_update(id)
    if requirements_changes:
        update_requirements()
    if migrations or requirements_changes:
        migrate(silent=True)

    collectstatic()

    restart_server(silent=True)


@task
def simple_deploy(id=None, silent=False):
    """ Perform a simple deploy to the target requested. """
    require('hosts')
    require('code_dir')

    # Show log of changes, return if nothing to do
    revset = show_log(id)
    if not revset:
        return

    migrations = migrate_diff(revset=revset, silent=True)
    if migrations:
        msg = "Found %d migrations; are you sure you want to continue with simple deploy?" % len(migrations)
        if not confirm(colors.yellow(msg), False):
            abort('Deployment aborted.')

    if not silent:
        request_confirm("simple_deploy")

    vcs_update(id)
    collectstatic()
    restart_server(silent=True)


@task
def online_deploy(id=None, silent=False):
    """ Perform an online deploy to the target requested. """
    require('hosts')
    require('code_dir')

    # Show log of changes, return if nothing to do
    revset = show_log(id)
    if not revset:
        return

    migrations = migrate_diff(revset=revset, silent=True)
    if migrations:
        print colors.yellow("Will apply %d migrations:" % len(migrations))
        print indent(migrations)

    if not silent:
        request_confirm("online_deploy")

    vcs_update(id)
    migrate(silent=True)
    collectstatic()
    restart_server(silent=True)


@task
def offline_deploy(id=None, silent=False):
    """ Perform an offline deploy to the target requested. """
    require('hosts')
    require('code_dir')

    # Show log of changes, return if nothing to do
    revset = show_log(id)
    if not revset:
        return

    migrations = migrate_diff(revset=revset, silent=True)
    if migrations:
        print colors.yellow("Will apply %d migrations:" % len(migrations))
        print indent(migrations)

    if not silent:
        request_confirm("offline_deploy")

    stop_server(silent=True)
    vcs_update(id)
    migrate(silent=True)
    collectstatic()
    start_server(silent=True)


@task
def setup_server():
    require('hosts')
    require('code_dir')
    require('nginx_conf')

    # Clone code repository
    vcs_clone()

    # Create password for DB, secret key and the local settings
    db_password = generate_password()
    secret_key = generate_password()
    local_settings = string.Template(PRODUCTION_LOCAL_SETTINGS).substitute(db_password=db_password, secret_key=secret_key)

    # Create database
    sudo('echo "CREATE DATABASE vorgupraxkaxpraxkax; '
         '      CREATE USER vorgupraxkaxpraxkax WITH password \'%s\'; '
         '      GRANT ALL PRIVILEGES ON DATABASE vorgupraxkaxpraxkax to vorgupraxkaxpraxkax;" '
         '| su -c psql postgres' % db_password)

    # Create virtualenv and install dependencies
    with cd(env.code_dir):
        # TODO: if you're not using Python 3.4, change or remove the -p argument
        sudo('virtualenv -p python3.4 venv')
    update_requirements()

    # Upload local settings
    put(local_path=StringIO(local_settings), remote_path=env.code_dir + '/vorgupraxkaxpraxkax/settings/local.py', use_sudo=True)

    # Create necessary dirs, with correct permissions
    mkdir_wwwdata('/var/log/vorgupraxkaxpraxkax/')
    with cd(env.code_dir + '/vorgupraxkaxpraxkax'), prefix('. ../venv/bin/activate'):
        mkdir_wwwdata('assets/CACHE/')
        mkdir_wwwdata('media/')

    # syncdb, migrations, collectstatic
    management_cmd('syncdb')
    management_cmd('migrate')
    collectstatic()

    # Ensure any and all created log files are owned by the www-data user
    sudo('chown -R www-data:www-data /var/log/vorgupraxkaxpraxkax/')

    # Copy nginx and gunicorn confs
    with cd(env.code_dir):
        sudo('cp deploy/%s /etc/nginx/sites-enabled/vorgupraxkaxpraxkax' % env.nginx_conf)
        sudo('cp deploy/gunicorn.conf /etc/init/gunicorn-vorgupraxkaxpraxkax.conf')

    # (Re)start services
    start_server(silent=True)

    # Restart nginx
    sudo('service nginx restart')


@task
def nginx_update():
    require('code_dir')
    require('nginx_conf')

    # Update nginx config
    with cd(env.code_dir):
        sudo('cp deploy/%s /etc/nginx/sites-enabled/vorgupraxkaxpraxkax' % env.nginx_conf)

    sudo('service nginx restart')


""" SERVER COMMANDS """


def stop_server(silent=False):
    if not silent:
        request_confirm("stop_server")

    require('service_name')
    require('code_dir')
    sudo("service %s stop" % env.service_name)


def start_server(silent=False):
    if not silent:
        request_confirm("start_server")

    require('service_name')
    require('code_dir')
    sudo("service %s start" % env.service_name)


def restart_server(silent=False):
    if not silent:
        request_confirm("restart_server")

    require('service_name')
    require('code_dir')
    sudo("service %s restart" % env.service_name)


@task
def management_cmd(cmd):
    """ Preform a management command on the target. """

    require('hosts')
    require('code_dir')

    sudo("cd %s ;"
         ". ./venv/bin/activate ; "
         "cd vorgupraxkaxpraxkax ; "
         "python manage.py %s" % (env.code_dir, cmd))


""" HELPERS """


@task
def repo_type():
    try:
        print("Current project is using: `%s`" % colors.green(get_repo_type()))

    except EnvironmentError:
        print("Current project is using: `%s`" % colors.red('NO VCS'))


def collectstatic():
    with cd(env.code_dir + '/vorgupraxkaxpraxkax'):
        sudo('bower install --production --allow-root')

    management_cmd('collectstatic --noinput')


def mkdir_wwwdata(path):
    # Creates directory and makes www-data its owner
    sudo('mkdir -p ' + path)
    sudo('chown www-data:www-data ' + path)


def request_confirm(tag):
    require('confirm_required')

    if env.confirm_required:
        if not confirm("Are you sure you want to run task: %s on servers %s?" % (tag, env.hosts)):
            abort('Deployment aborted.')


def generate_password(length=50):
    # Similar to Django's charset but avoids $ to avoid accidential shell variable expansion
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#%^&*(-_=+)'
    return get_random_string(length, chars)


""" VCS HELPERS """


def git_get_branch():
    with cd(env.code_dir), hide('running'):
        return sudo('git rev-parse --abbrev-ref HEAD', quiet=True)


def get_repo_type():
    """ Get current repository type, by checking
        if .git or .hg exists on the parent path.

    :return: hg|git
    """

    if os.path.exists(os.path.join('..', '.git')):
        return 'git'

    elif os.path.exists(os.path.join('..', '.hg')):
        return 'hg'

    else:
        raise EnvironmentError('No suitable VCS root detected')


def get_version(vcs_type=None):
    """ Get current vcs version in the remote server.

    :param vcs_type: hg|git
    :return:
    """

    if vcs_type is None:
        vcs_type = get_repo_type()

    command = {
        'hg': 'hg id -nib',
        'git': "git log -n 1 --oneline --format='%h %s - %an'",
    }

    with cd(env.code_dir), hide('running'):
        result = run(command[vcs_type], quiet=True)

    return result


def vcs_clone(vcs_type=None):
    """ Clone a repository remotely based on the vcs type

    :param vcs_type: hg|git
    :return:
    """

    if vcs_type is None:
        vcs_type = get_repo_type()

    command = {
        'hg': 'hg paths default',
        'git': 'git config --get remote.origin.url',
    }

    vcs_url = local(command[vcs_type], capture=True)
    assert vcs_url
    sudo('%s clone %s %s' % (vcs_type, vcs_url, env.code_dir))


def vcs_log(commit_id, vcs_type=None):
    require('code_dir')

    if vcs_type is None:
        vcs_type = get_repo_type()

    def run_vcs_log(revs):
        """ Returns lines returned by hg|git log, as a list (one revision per line). """
        command = {
            'hg': "hg log --template '{rev}:{node|short} {branch} {desc|firstline}\\n' -r '%s'",
            'git': "git --no-pager log %s --oneline --format='%%h %%s - %%an'",
        }

        result = sudo(command[vcs_type] % revs)
        return result.split('\n') if result else []

    def get_revset(x, y):
        assert x or y
        if x and y:
            # All revisions that are descendants of the current revision and ancestors of the target revision
            #  (inclusive), but not the current revision itself
            return '%s%s%s' % (x, '::' if vcs_type == 'hg' else '..', y)
        else:
            # All revisions that are in the current branch, are descendants of the current revision and are not the
            #  current revision itself.
            if vcs_type == 'hg':
                return 'branch(p1()) and %s::%s' % (x or '', y or '')

            else:
                raise NotImplementedError('With git, get_revset should always get x and y')

    if vcs_type == 'git' and not commit_id:
        # For git, we need to manually specify we want the tip of origin
        commit_id = 'origin/%s' % git_get_branch()

    with cd(env.code_dir), hide('running', 'stdout'):
        # First do vcs pull
        vcs_pull()

        revision_set = get_revset('.' if vcs_type == 'hg' else ' ', commit_id)
        revisions = run_vcs_log(revision_set)

        def get_revisions(x):
            x = x[1:] if vcs_type == 'hg' else x

            if vcs_type == 'git':
                x = list(reversed(x))

            return x

        if len(revisions) > 1 or (len(revisions) == 1 and vcs_type == 'git'):
            # Target is forward of the current rev
            return {'forwards': get_revisions(revisions), 'revset': revision_set}

        elif vcs_type == 'hg' and len(revisions) == 1:
            # Current rev is the same as target: only for HG
            return {'message': "Already at target revision"}

        # Check if target is backwards of the current rev
        revision_set = get_revset(commit_id, '.' if vcs_type == 'hg' else ' ')
        revisions = run_vcs_log(revision_set)

        if revisions:
            return {'backwards': reversed(get_revisions(revisions)), 'revset': revision_set}

        else:
            if vcs_type == 'hg':
                return {'message': "Target revision is not related to the current revision"}

            else:
                return {'message': "Already at target revision"}


def changed_files(revision_set, filter_re=None, vcs_type=None):
    """
    Returns list of files that changed in the given revset, optionally filtered by the given regex or array of regex values.
    """
    require('code_dir')

    if vcs_type is None:
        vcs_type = get_repo_type()

    with cd(env.code_dir):
        cmd = {
            'hg': "hg status --rev '%s'",
            'git': "git --no-pager diff --name-status %s",
        }

        result = run(cmd[vcs_type] % revision_set, quiet=True).splitlines()

        if vcs_type == 'git':
            result = map(lambda x: re.sub(r'^([A-Z]+)\t', r'\1    ', x), result)

        if filter_re:
            def finder(pattern):
                regex = re.compile(pattern)

                return filter(lambda filename: regex.search(filename), result)

            if isinstance(filter_re, (list, tuple)):
                full_result = []

                for reg in filter_re:
                    for res in finder(reg):
                        full_result.append(res)

                result = full_result

            else:
                result = finder(filter_re)

        return result


def vcs_pull(vcs_type=None):
    if vcs_type is None:
        vcs_type = get_repo_type()

    command = {
        'hg': 'hg pull',
        'git': 'git fetch',
    }

    with cd(env.code_dir):
        sudo("%(cmd)s %(vcs_extra)s" % {
            "cmd": command[vcs_type],
            "vcs_extra": env.vcs_extra,
        })


def vcs_update(revision='', vcs_type=None):
    if vcs_type is None:
        vcs_type = get_repo_type()

    if vcs_type == 'git' and not revision:
        # For git, we need to manually specify we want the tip of origin
        revision = 'origin/%s' % git_get_branch()

    command = {
        'hg': 'hg update',
        'git': 'git checkout',
    }

    with cd(env.code_dir):
        sudo("%(cmd)s %(rev)s" % {
            "cmd": command[vcs_type],
            "rev": revision if revision else '',
        })
