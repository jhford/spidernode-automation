#!/bin/false

from subprocess import Popen
import os
import sys
import time

class CommandTimeoutExceeded(Exception):
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




