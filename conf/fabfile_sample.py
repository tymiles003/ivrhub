'''
fabfile_sample
edit this to your satisfaction then place it in your project root as fabfile.py
usage:
    $ fab dev pack deploy
    $ fab dev uptime
'''
import os
from fabric.api import *

def prod():
    env.user = 'brucewayne'
    env.hosts = ['brahe']
    env.virtualenv_dir = '/home/bruce/conf/virtualenvs/hawthorne'
    env.project_dir = '/home/bruce/hawthorne'
    env.supervisord_config = '/home/bruce/conf/hawthorne/supervisord.conf'
    env.branch = 'master'


def pack():
    # create a new source distribution as a tarball
    local('python setup.py sdist --formats=gztar', capture=False)


def deploy():
    # determine release name and version
    dist = local('python setup.py --fullname', capture=True).strip()
    # upload the source tarball and unzip
    put('dist/%s.tar.gz' % dist, '/tmp/hawthorne.tar.gz')
    run('mkdir /tmp/hawthorne')
    with cd('/tmp/hawthorne'):
        run('tar xzf /tmp/hawthorne.tar.gz')
        # setup the package with the virtualenv
        python = os.path.join(env.virtualenv_dir, 'bin/python')
        run('%s setup.py install' % python)
        # re-install requirements.txt
        # tbd..

    # delete the temporary folder
    run('rm -rf /tmp/hawthorne /tmp/hawthorne.tar.gz')

    # restart the server..


def logs():
    ''' view logs
    supervisord redirects stderr and stdout to this path
    '''
    run('tail /tmp/hawthorne.log')


def gunicorn(command):
    ''' gunicorn controls via supervisord
    '''
    if command == 'start':
        run('supervisorctl -c %s start gunicorn' % env.supervisord_config)
    elif command == 'stop':
        run('supervisorctl -c %s stop gunicorn' % env.supervisord_config)
    elif command == 'restart':
        run('supervisorctl -c %s restart gunicorn' % env.supervisord_config)
    elif command == 'status':
        run('supervisorctl -c %s status gunicorn' % env.supervisord_config)
    else:
        print 'sorry, did not understand that gunicorn command'


def nginx(command):
    ''' nginx controls
    '''
    if command == 'start':
        sudo('/etc/init.d/nginx start')
    elif command == 'stop':
        sudo('/etc/init.d/nginx stop')
    elif command == 'restart':
        nginx('stop')
        nginx('start')
    else:
        print 'hm, did not quite understand that nginx command'


''' misc
'''
def host_info():
    print 'checking lsb_release of host: '
    run('lsb_release -a')

def uptime():
    run('uptime')

def grep_python():
    run('ps aux | grep python')
