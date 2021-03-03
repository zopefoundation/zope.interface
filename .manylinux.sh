#!/usr/bin/env bash

set -e -x

# Mount the current directory as /io
# Mount the pip cache directory as /cache
# `pip cache` requires pip 20.1
echo Setting up caching
python --version
python -mpip --version
LCACHE="$(dirname `python -mpip cache dir`)"
echo Sharing pip cache at $LCACHE $(ls -ld $LCACHE)

docker run --rm -e GITHUB_ACTIONS -v "$(pwd)":/io -v "$LCACHE:/cache" $DOCKER_IMAGE $PRE_CMD /io/.manylinux-install.sh
