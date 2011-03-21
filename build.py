#!/bin/false

from subprocess import Popen
from optparse import OptionParser
import os
import posixpath, ntpath
import sys
import time
import shutil # for rm()

class CommandTimeoutExceeded(Exception):
    pass

class CommandNotFoundException(Exception):
    pass

def run_cmd(args, workdir='.', env={}, timeout=60*60*45):
    workdir_exists = os.path.isdir(workdir)
    if not workdir_exists:
        os.makedirs(workdir)
    print "=" * 80
    print "CMD:     %s" % args[0]
    print "ARGS:    %s" % args[1:], '' if workdir_exists else '(created)'
    print "PWD:     %s" % os.getcwd()
    print "WORKDIR: %s" % workdir
    print "^" * 80
    client_env = dict(os.environ)
    client_env.update(env)
    sys.stdout.flush()
    sys.stderr.flush()
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
    sys.stdout.flush()
    sys.stderr.flush()
    end = time.time()
    print "$" * 80
    signal_string = ''
    if rc < 0:
        signal_string = " KILLED BY SIGNAL %d" % -rc
    print "RC:      %d" % rc, signal_string
    print "TIME:    %.2fs" % float(end - start)
    if exception:
        raise exception
    return rc

def make(workdir='.', target=None, makefile=None, keep_going=False,
         directory=None, make_bin='make', **kwargs):
    args = [make_bin]
    if makefile:
        args.extend(['-f', makefile])
    if keep_going:
        args.append('-k')
    if directory:
        args.extend(['-C', directory])
    return run_cmd(args=args, workdir=workdir, **kwargs)

def rm(to_remove):
    """This should be replaced with something that works better on windows"""
    if issubclass(type(to_remove), type("")):
        to_remove = [to_remove]
    print "=" * 80
    print "REMOVING FILES"
    print "^" * 80
    start = time.time()
    for item in to_remove:
        if os.path.isdir(item) or os.path.isfile(item):
            print "REMOVING: %s" % item
            shutil.rmtree(item)
            print "REMOVED:  %s" % item
    end = time.time()
    print "$" * 80
    print "TIME:    %.2fs" % float(end - start)

def find_cmd(names, nt=None):
    """Search for programs in 'names' and return the first match
    as a string.  This function prioritizes order in names arg"""
    if None == nt:
        pathmod = os.path
    else:
        if nt == True:
            pathmod = ntpath
        else:
            pathmod = posixpath
    if pathmod is ntpath:
        pathsep = ';'
    else:
        pathsep = ':'
    path = os.environ['PATH']
    path_dirs = path.split(pathsep)
    attempts=[]
    for name in names:
        for path_dir in path_dirs:
            potential = pathmod.join(path_dir, name)
            if pathmod.isfile(potential):
                if os.access(potential, os.X_OK):
                    return potential
                else:
                    attempts('NO_EXEC:%s' % potential)
            else:
                attempts.append(potential)
    raise CommandNotFoundException(
        'no command with names in %s in path %s was found.\ntried %s' % \
        (names, path_dirs, attempts)
    )

def main():
    parser = OptionParser()
    parser.add_option("--build-style", dest="bld_style",
                      help="build style, opt or debug for now")
    parser.add_option("--build-nspr", dest="bld_nspr",
                      action='store_true',
                      help="should we build nspr")
    (options, args) = parser.parse_args()
    if args.bld_nspr:
        build_nspr
    build_js()

def build_js(objdir='objdir', prefix='usr', conf_args=[]):
    conf_args = conf_args[:]
    conf_args.append("--prefix=%s" % prefix)
    shell_bin = find_cmd(['bash', 'sh'])
    make_bin = find_cmd(['make', 'gmake'])
    rm(objdir)
    autoconf_bin = find_cmd(['autoconf-2.13', 'autoconf213'])
    run_cmd([autoconf_bin], workdir='build/js/src')
    run_cmd([shell_bin,
             '../build/js/src/configure %s' % ' '.join(conf_args)],
             workdir=objdir)
    make(workdir=objdir, make_bin=make_bin)

if __name__ == "__main__":
    main()

















