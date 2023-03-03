#!/usr/bin/env bash
# Generated from:
# https://github.com/zopefoundation/meta/tree/master/config/c-code

set -e -x

# Running inside docker
# Set a cache directory for pip. This was
# mounted to be the same as it is outside docker so it
# can be persisted.
export XDG_CACHE_HOME="/cache"
# XXX: This works for macOS, where everything bind-mounted
# is seen as owned by root in the container. But when the host is Linux
# the actual UIDs come through to the container, triggering
# pip to disable the cache when it detects that the owner doesn't match.
# The below is an attempt to fix that, taken from bcrypt. It seems to work on
# Github Actions.
if [ -n "$GITHUB_ACTIONS" ]; then
    echo Adjusting pip cache permissions
    mkdir -p $XDG_CACHE_HOME/pip
    chown -R $(whoami) $XDG_CACHE_HOME
fi
ls -ld /cache
ls -ld /cache/pip

# We need some libraries because we build wheels from scratch:
yum -y install libffi-devel

tox_env_map() {
    case $1 in
        *"cp312"*) echo 'py312';;
        *"cp37"*) echo 'py37';;
        *"cp38"*) echo 'py38';;
        *"cp39"*) echo 'py39';;
        *"cp310"*) echo 'py310';;
        *"cp311"*) echo 'py311';;
        *) echo 'py';;
    esac
}

# Compile wheels
for PYBIN in /opt/python/*/bin; do
    if \
       [[ "${PYBIN}" == *"cp312"* ]] || \
       [[ "${PYBIN}" == *"cp311"* ]] || \
       [[ "${PYBIN}" == *"cp37"* ]] || \
       [[ "${PYBIN}" == *"cp38"* ]] || \
       [[ "${PYBIN}" == *"cp39"* ]] || \
       [[ "${PYBIN}" == *"cp310"* ]] ; then
        if [[ "${PYBIN}" == *"cp312"* ]] ; then
            "${PYBIN}/pip" install --pre -e /io/
            "${PYBIN}/pip" wheel /io/ --pre -w wheelhouse/
        else
            "${PYBIN}/pip" install -e /io/
            "${PYBIN}/pip" wheel /io/ -w wheelhouse/
        fi
        if [ `uname -m` == 'aarch64' ]; then
          cd /io/
          ${PYBIN}/pip install tox
          TOXENV=$(tox_env_map "${PYBIN}")
          ${PYBIN}/tox -e ${TOXENV}
          cd ..
        fi
        rm -rf /io/build /io/*.egg-info
    fi
done

# Bundle external shared libraries into the wheels
for whl in wheelhouse/zope.interface*.whl; do
    auditwheel repair "$whl" -w /io/wheelhouse/
done
