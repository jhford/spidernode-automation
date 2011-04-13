#!/bin/sh
run_cmd () {
    echo "=========================="
    echo "ARGS: '$@'"
    echo "PWD:  '$PWD'"
    echo $(date "+%s") - START
    echo "^^^^^^^^^^^^^^^^^^^^^^^^^^"
    "$@"
    rc="$?"
    if [[ $rc -ne 0 ]] ; then
        fatal "running command $@"
    fi
    echo '$$$$$$$$$$$$$$$$$$$$$$$$$$'
    echo "RC:    $rc"
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

OBJDIR=$PWD/objdir
PROBJDIR="$OBJDIR-nspr"
PREFIX=$PWD/usr

for i in autoconf-2.13 autoconf213 ; do
    if $i --version &> /dev/null ; then
        AUTOCONF=$i
        break
    fi
done
for i in make gmake ; do
    if $i --version &> /dev/null ; then
        MAKE=$i
        break
    fi
done
for i in bash sh ; do
    if $i --version &> /dev/null ; then
        SHELL=$i
        break
    fi
done

if [[ "x" == "x$PLATFORM" ]] ; then
    fatal You must specify a platform
fi
if [[ "x" == "x$STYLE" ]] ; then
    fatal You must specify a build type
fi

conf_args="--prefix=$PREFIX --enable-tests"

case $STYLE in
    "opt" )
        conf_args="$conf_args --enable-optimize --disable-debug"
        ;;
    "debug" )
        conf_args="$conf_args --disable-optimize --enable-debug"
esac

case $PLATFORM in
    "x86_64-win32" )
        conf_args="$conf_args --target=x86_64-pc-mingw32"
        ;;
esac

info Doing a $PLATFORM-$STYLE build
test -d build/js/src || fatal missing source
test -d build/nsprpub || fatal missing source
run_cmd rm -rf $OBJDIR $PROBJDIR $PREFIX
run_cmd mkdir -p $OBJDIR $PROBJDIR
#This is to remove older builder directories
run_cmd rm -rf ../*-master-opt ../*-master-debug ../*-v8-api-tests-opt ../*-v8-api-tests-debug

# Build nspr
pushd build/nsprpub > /dev/null
run_cmd $AUTOCONF
popd > /dev/null
pushd $PROBJDIR > /dev/null
nspr_conf="--with-dist-prefix=$PROBJDIR/dist --with-mozilla"
if ! run_cmd ../build/nsprpub/configure $conf_args $nspr_conf ; then
    fatal running nspr configure
fi
run_cmd $MAKE
run_cmd $MAKE install
popd > /dev/null



# Build spidermonkey
pushd build/js/src > /dev/null
run_cmd $AUTOCONF
popd > /dev/null
pushd $OBJDIR > /dev/null
pr_cflags="$($PREFIX/bin/nspr-config --cflags)"
echo $PLATFORM | grep win32 &> /dev/null
if [[ $? -eq 0 ]] ; then
    pr_libs=""
    for i in plds4.lib plc4.lib nspr4.lib ; do
        pr_libs="$pr_libs $PREFIX/lib/$i"
    done
else
    pr_libs=$($PREFIX/bin/nspr-config --libs)
fi
run_cmd ../build/js/src/configure $conf_args \
     --with-nspr-libs=\'"$pr_libs"\' --with-nspr-cflags=\'"$pr_cflags"\'
run_cmd $MAKE
run_cmd $MAKE install
popd > /dev/null













