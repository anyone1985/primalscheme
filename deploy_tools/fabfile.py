import random

from fabric.contrib.files import append, exists, sed
from fabric.api import env, local, run, put

REPO_URL = 'https://github.com/aresti/primalscheme'


def deploy():
    site_folder = '/home/%s/sites/%s' % (env.user, env.host)
    source_folder = site_folder + '/primal'
    local_source_folder = '../primal'
    _get_latest_source(site_folder)
    _create_directory_structure(site_folder)
    _copy_local_settings(local_source_folder, source_folder)
    _update_settings(source_folder, env.host)
    _update_virtualenv(site_folder)
    _update_static_files(source_folder)
    _update_database(source_folder)
    _restart_gunicorn(env.host)
    _restart_nginx()


def _create_directory_structure(site_folder):
    for subfolder in ('database', 'static', 'venv'):
        run('mkdir -p %s/%s' % (site_folder, subfolder))


def _copy_local_settings(local_source_folder, source_folder):
    put(local_source_folder + '/primal/settings_local.py',
        source_folder + '/primal/settings_local.py')


def _get_latest_source(site_folder):
    run('mkdir -p %s' % (site_folder,))
    if exists(site_folder + '/.git'):
        run('cd %s && git fetch' % (site_folder,))
    else:
        run('git clone --recursive %s %s' % (REPO_URL, site_folder))
    current_commit = local("git log -n 1 --format=%H", capture=True)
    run('cd %s && git reset --hard %s' % (site_folder, current_commit))
    run('cd %s && git submodule update --init' % (site_folder))


def _update_settings(source_folder, site_name):
    settings_path = source_folder + '/primal/settings.py'
    sed(settings_path, "DEBUG = True", "DEBUG = False")
    sed(settings_path,
        'ALLOWED_HOSTS =.+$',
        'ALLOWED_HOSTS = ["%s"]' % (site_name,)
    )


def _update_virtualenv(site_folder):
    virtualenv_folder = site_folder + '/venv'
    if not exists(virtualenv_folder + '/bin/pip'):
        run('virtualenv --python=python2.7 %s' % (virtualenv_folder,))
    run('%s/bin/pip install -r %s/requirements.txt' % (
        virtualenv_folder, site_folder
    ))


def _update_static_files(source_folder):
    run('cd %s && ../venv/bin/python2.7 manage.py collectstatic --noinput' % (
        source_folder,
    ))


def _update_database(source_folder):
    run('cd %s && ../venv/bin/python2.7 manage.py migrate --noinput' % (
        source_folder,
    ))


def _restart_gunicorn(site_name):
    run('sudo systemctl restart gunicorn-%s' % (site_name,))


def _restart_nginx():
    run('sudo service nginx restart')
