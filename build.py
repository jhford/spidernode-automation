#!/bin/false

from subprocess import Popen
import os
import posixpath, ntpath
import sys
import time

class CommandTimeoutExceeded(Exception):
    pass

class CommandNotFoundException(Exception):
    pass

def run_cmd(args, workdir='.', env={}, timeout=30):
    print "=" * 80
    print "CMD:  %s" % args[0]
    print "ARGS: %s" % args[1:]
    print "CWD:  %s" % workdir
    print "^" * 80
    client_env = dict(os.environ)
    client_env.update(env)
    p = Popen(args, stdin=sys.stdin, stdout=sys.stdout,
                   stderr=sys.stderr, cwd=workdir, env=client_env,)
    start = time.time()
    exception = None
    while None == p.poll():
        now = time.time()
        if (now - start) > timeout:
            exception = CommandTimeoutExceeded("timeout exceeded for %s" % args)
            p.terminate()
            break
    rc = p.wait()
    end = time.time()
    print "$" * 80
    signal_string = ''
    if rc < 0:
        signal_string = " KILLED BY SIGNAL %d" % -rc
    print "RC:   %d" % rc, signal_string
    print "TIME: %.2fs" % float(end - start)
    if exception:
        raise exception
    return rc

def make(workdir='.', target=None, makefile=None, keep_going=False,
         directory=None, make_bin="make", **kwargs):
    args = [make_bin]
    if makefile:
        args.extend(['-f', makefile])
    if keep_going:
        args.append('-k')
    if directory:
        args.extend(['-C', directory])
    return run_cmd(args=args, workdir=workdir, **kwargs)

def find_cmd(names, nt=False):
    """Search for programs in 'names' and return the first match
    as a string.  This function prioritizes order in names arg"""
    if nt:
        pathmod = ntpath
    else:
        pathmod = posixpath
    path = os.environ['PATH']
    path_dirs = path.split(';' if nt else ':')
    for name in names:
        for path_dir in path_dirs:
            potential = pathmod.join(path_dir, name)
            if pathmod.isfile(potential) and os.access(potential, os.X_OK):
                return potential
    raise CommandNotFoundException(
        'no command in %s with path %s was found' % \
        (names, path_dirs)
    )

print find_cmd(['bash', 'sh'])
print find_cmd(['make', 'gmake'])
print find_cmd(['python2.7', 'python2.6', 'python2.5', 'python2', 'python'])
print find_cmd(['autoconf-2.13', 'autoconf213'])



