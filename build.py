#!/bin/echo specify python interpreter explicitly for

from subprocess import Popen
from optparse import OptionParser
import os
import posixpath, ntpath
import sys
import time
import re
import shutil # for rm()

class CommandTimeoutExceeded(Exception):
    pass

class CommandNotFoundException(Exception):
    pass

class CommandFailedException(Exception):
    pass

def sysflush():
    sys.stdout.flush()
    sys.stderr.flush()

def run_cmd(args, workdir='.', env={}, fatal=True, timeout=60*60*45):
    if os.name == 'nt':
        workdir = workdir.replace("/", "\\")
    workdir_exists = os.path.isdir(workdir)
    if not workdir_exists:
        os.makedirs(workdir)
    print "=" * 80
    print "CMD:     %s" % args[0]
    print "ARGS:    %s" % args[1:]
    print "PWD:     %s" % os.getcwd()
    print "WORKDIR: %s" % workdir, '' if workdir_exists else '(created)'
    print "^" * 80
    sysflush()
    client_env = dict(os.environ)
    client_env.update(env)
    p = Popen(args, shell=(os.name == 'nt'), stdin=sys.stdin, stdout=sys.stdout,
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
    sysflush()
    end = time.time()
    print "$" * 80
    signal_string = ''
    if rc < 0:
        signal_string = " KILLED BY SIGNAL %d" % -rc
    print "RC:      %d" % rc, signal_string
    print "TIME:    %.2fs" % float(end - start)
    sysflush()
    if exception:
        raise exception
    if rc != 0 and fatal:
        raise CommandFailedException('command "%s" failed' % args)
    return rc

def make(workdir='.', target=None, makefile=None, keep_going=False,
         directory=None, make_bin='make', make_vars={}, **kwargs):
    args = [make_bin]
    if makefile:
        args.extend(['-f', makefile])
    if keep_going:
        args.append('-k')
    if directory:
        args.extend(['-C', directory])
    for key in make_vars.keys():
        args.append("%s=%s" % (key, make_vars[key]))
    return run_cmd(args=args, workdir=workdir, **kwargs)

def rm(to_remove):
    """This should be replaced with something that works better on windows"""
    if issubclass(type(to_remove), type("")):
        to_remove = [to_remove]
    print "=" * 80
    print "REMOVING FILES"
    print "^" * 80
    sysflush()
    start = time.time()
    for item in to_remove:
        if os.path.isdir(item) or os.path.isfile(item):
            print "REMOVING: %s" % item
            sysflush()
            shutil.rmtree(item)
            print "REMOVED:  %s" % item
            sysflush()
    end = time.time()
    print "$" * 80
    print "TIME:    %.2fs" % float(end - start)
    sysflush()

def find_cmd(names, nt=None):
    """Search for programs in 'names' and return the first match
    as a string.  This function prioritizes order in names arg"""
    names = names[:] #don't modify caller's copy
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
    if os.name == 'nt':
        win_names = []
        for name in names:
            #should I also iterate over %PATHEXT% ?
            extpath = os.environ['PATHEXT']
            exts = extpath.split(';')
            win_names.extend(["%s%s" % (name, x) for x in exts] + [name])
        names = win_names
    for name in names:
        for path_dir in path_dirs:
            potential = pathmod.join(path_dir, name)
            if pathmod.isfile(potential):
                if os.access(potential, os.X_OK):
                    return potential
                else:
                    attempts('NO_EXEC:%s' % potential)
            else:
                attempts.append('NO_FILE:%s' % potential)
    raise CommandNotFoundException(
        'no command with names in %s in path %s was found.\ntried %s' % \
        (names, path_dirs, attempts)
    )

def main():
    parser = OptionParser()
    parser.add_option("--build-style", dest="build_style",
                      help="build style, opt or debug for now")
    (options, args) = parser.parse_args()
    conf_args = []
    if options.build_style == "opt":
        conf_args.extend(["--enable-optimize",
                          "--disable-debug",
                          "--enable-tests"])
    elif options.build_style == "debug":
        conf_args.extend(["--enable-tests",
                          "--enable-debug",
                          "--disable-optimize"])
    else:
        print >> sys.stderr, "BUILD-ERROR: only 'opt' and 'debug' are supported"
        sysflush()
        exit(1)
    return build()

def build(objdir='objdir', prefix='usr', conf_args=[]):
    # This variable is set to 0, every function should
    # add its return code to it.  Hacky, but the final
    # portion of this function checks if this is non-zero
    # and either sets a return code of 1 or 0
    rc = 0

    # sys_objdir is an absolute path to the objdir
    # that the host system understands (i.e. windows
    # style on windows
    sys_objdir = os.path.abspath(objdir)

    # posix_objdir is an absolute path to the objdir
    # that is written in a format that is understood
    # by posix programs.  On windows, c:\file becomes
    # /c/file
    if os.name == 'nt':
         (drive, tail) = ntpath.splitdrive(sys_objdir)
         posix_objdir = '/%s' % drive[0]
         parts = []
         while tail.count('\\') > 1:
             (head, tail) = ntpath.split(tail)
             parts.insert(0, tail)
             tail = head # make our head the next iteration's tail
         parts.insert(0, tail.replace('\\', '', 1))
         for part in parts:
             posix_objdir = posixpath.join(posix_objdir, part)
    else:
        posix_objdir = sys_objdir


    # Configure arguments shared between js and nspr
    conf_args = conf_args[:]
    conf_args.append("--prefix=%s/dist" % sys_objdir)
    conf_args.append("--with-dist-prefix=%s/dist" % sys_objdir)

    # nspr specific configure arguments
    nspr_conf_args = conf_args[:]
    nspr_conf_args.append("--with-mozilla")

    # js specific configure arguments
    js_conf_args = conf_args[:]
    if os.name == 'nt':
        libs = ['%s/%s' % (posix_objdir, x) for x in ('plds4.lib', 'plc4.lib', 'nspr4.lib')]
        js_conf_args.extend(['--with-nspr-prefix=%s/dist/',
                             '--with-nspr-cflags=$(%s/dist/bin/nspr-config --cflags)' % sys_objdir,
                             '--with-nspr-libs="%s"' % libs,
                            ])
    else:
        js_conf_args.extend(['--with-nspr-prefix=%s/dist/',
                             '--with-nspr-cflags=$(%s/dist/bin/nspr-config --cflags)' % posix_objdir,
                             '--with-nspr-libs=$(%s/dist/bin/nspr-config --libs)' % posix_objdir,
                            ])

    shell_bin = find_cmd(['bash', 'sh'])
    make_bin = find_cmd(['make', 'gmake'])
    autoconf_bin = find_cmd(['autoconf-2.13', 'autoconf213'])
    rm(objdir)
    rc += run_cmd([shell_bin, autoconf_bin], workdir='build/nsprpub')
    rc += run_cmd([shell_bin, '../build/nsprpub/configure'] + nspr_conf_args,
                                   workdir=sys_objdir)
    rc += make(workdir=sys_objdir, make_bin=make_bin,
               make_vars={'OBJDIR': posix_objdir})
    rc += make(workdir=objdir, make_bin=make_bin, target='install')
    rc += run_cmd([shell_bin, autoconf_bin], workdir='build/js/src')
    rc += run_cmd([shell_bin, '../build/js/src/configure'] + js_conf_args,
                                   workdir=sys_objdir)
    rc += make(workdir=objdir, make_bin=make_bin)
    return int(rc != 0)

if __name__ == "__main__":
    exit(main())

















