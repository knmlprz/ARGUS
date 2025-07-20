#!/bin/bash

set -e

cd /TrailblazerML

# ponizsze komendy są zakomentowane bo rosdep i colcon na ten moment musza 
# byc bezposrednio w terminalu uruchomione nie w tym entrypoint

#rosdep install --from-paths src --ignore-src -r -y

SETUP_BASH="install/setup.bash"

if [ ! -d "install" ]; then
    echo "Workspace not built. Building with colcon"
    #colcon build
else
    echo "Workspace already built"
fi

if [ -f "$SETUP_BASH" ]; then
    # shellcheck disable=SC1090
    #source install/setup.bash
    echo "tak"
else
    echo "$SETUP_BASH does not exist. Please build your workspace first."
    exit 1
fi
cd /TrailblazerML
terminator
exec "$@"