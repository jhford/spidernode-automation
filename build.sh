#!/bin/sh

run_cmd () {
    echo "=========================="
    echo "ARGS: $@"
    echo "PWD:  '$PWD'"
    echo $(date "+%s") - START
    echo "^^^^^^^^^^^^^^^^^^^^^^^^^^"
    "$@"
    echo "$$$$$$$$$$$$$$$$$$$$$$$$$$"
    echo "RC:    $?"
    echo $(date "+%s") - END
}

info() {
    echo "BUILD-INFO: $@"
}

warn() {
    echo "BUILD-WARN: $@"
}

error() {
    echo "BUILD-ERROR: $@"
}

fatal() {
    echo "BUILD-FATAL-ERROR: $@"
    exit 66
}

info Starting v8monkey build
PLATFORM=$1
STYLE=$2
OBJDIR=objdir

# need to make this work for non-fedora
AUTOCONF=autoconf-2.13
MAKE=make
SHELL=bash


if [[ "x" == "x$PLATFORM" ]] ; then
    fatal You must specify a platform
fi
if [[ "x" == "x$STYLE" ]] ; then
    fatal You must specify a build type
fi
info Doing a $PLATFORM-$STYLE build
test -d build/js/src || fatal missing source
run_cmd rm -rf $OBJDIR
mkdir $OBJDIR
#This is to remove older builder directories
run_cmd rm -rf ../*-master-debug ../*-master-debug ../*-v8-api-tests-opt ../*-v8-api-tests-debug
pushd build/js/src > /dev/null
run_cmd $AUTOCONF
popd > /dev/null
mkdir -p $OBJDIR
pushd $OBJDIR > /dev/null
run_cmd $SHELL ../build/js/src/configure
run_cmd $MAKE
popd > /dev/null
