'''
fabfile_sample.py
edit this to your satisfaction, then move it in your project root as fabfile.py
usage:
    $ fab dev pack deploy
    $ fab dev uptime
'''
import os
from fabric.api import *

def dev():
    env.user = 'nathaniel'
    env.hosts = ['tycho']
    env.virtualenv_dir = '/home/nathaniel/conf/virtualenvs/ivrhub'
    env.supervisord_config = '/home/nathaniel/conf/tycho/supervisord.conf'


def pack():
    # create a new source distribution as a tarball
    local('python setup.py sdist --formats=gztar', capture=False)


def deploy():
    # determine release name and version
    dist = local('python setup.py --fullname', capture=True).strip()
    # upload the source tarball and unzip
    put('dist/%s.tar.gz' % dist, '/tmp/ivrhub.tar.gz')
    run('mkdir /tmp/ivrhub')
    with cd('/tmp/ivrhub'):
        run('tar xzf /tmp/ivrhub.tar.gz')
        # setup the package with the virtualenv
        
        with cd('/tmp/ivrhub/%s' % dist):
            python = os.path.join(env.virtualenv_dir, 'bin/python')
            run('%s setup.py install' % python)

            # re-install requirements.txt
            run('pip install -r requirements.txt -E %s' % env.virtualenv_dir)

    # delete the temporary folder
    run('rm -rf /tmp/ivrhub/tmp/ivrhub.tar.gz')

    # restart the server..
    run('supervisorctl restart ivrhub')


def logs():
    ''' view logs
    supervisord redirects stderr and stdout to this path
    '''
    run('tail /tmp/ivrhub.log')


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
