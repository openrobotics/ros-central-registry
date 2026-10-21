#!/usr/bin/env bash
# --- begin runfiles.bash initialization v2 ---
# Copy-pasted from the Bazel Bash runfiles library v2.
set -uo pipefail; f=bazel_tools/tools/bash/runfiles/runfiles.bash
source "${RUNFILES_DIR:-/dev/null}/$f" 2>/dev/null || \
  source "$(grep -sm1 "^$f " "${RUNFILES_MANIFEST_FILE:-/dev/null}" | cut -f2- -d' ')" 2>/dev/null || \
  source "$0.runfiles/$f" 2>/dev/null || \
  source "$(dirname "$0")/$f" 2>/dev/null || \
  source "$(dirname "$0")/../$f" 2>/dev/null || \
  { echo>&2 "ERROR: cannot find $f"; exit 1; }
# --- end runfiles.bash initialization v2 ---

find_runfile() {
  local p
  for candidate in "$@"; do
    p=$(rlocation "$candidate" 2>/dev/null || true)
    if [[ -n "$p" && -e "$p" ]]; then
      echo "$p"
      return 0
    fi
    if [[ -n "${RUNFILES_DIR:-}" && -e "${RUNFILES_DIR}/${candidate}" ]]; then
      echo "${RUNFILES_DIR}/${candidate}"
      return 0
    fi
  done
  return 1
}

gz_rb=$(find_runfile "gz-tools/gz.rb" "gz-tools+/gz.rb" "gz/gz.rb")
sim_yaml=$(find_runfile "gz-tools/sim.yaml" "gz-tools+/sim.yaml" || true)
cmdsim_rb=$(find_runfile "gz-tools/cmdsim.rb" "gz-tools+/cmdsim.rb" || true)
gui_yaml=$(find_runfile "gz-gui/conf/gui.yaml" "gz-gui+/conf/gui.yaml")
cmdgui_rb=$(find_runfile "gz-gui/src/cmd/cmdgui.rb" "gz-gui+/src/cmd/cmdgui.rb")
libgz_gui=$(find_runfile "gz-gui/libgz-gui-shared.so" "gz-gui+/libgz-gui-shared.so")

if [[ -z "$gz_rb" || -z "$gui_yaml" || -z "$cmdgui_rb" || -z "$libgz_gui" ]]; then
  echo >&2 "ERROR: missing runfiles. Make sure to build with all dependencies."
  echo >&2 "gz_rb: $gz_rb"
  echo >&2 "gui_yaml: $gui_yaml"
  echo >&2 "cmdgui_rb: $cmdgui_rb"
  echo >&2 "libgz_gui: $libgz_gui"
  exit 1
fi

export GZ_CONFIG_PATH=$(dirname "$gui_yaml")${GZ_CONFIG_PATH:+:$GZ_CONFIG_PATH}
if [[ -n "$sim_yaml" ]]; then
  export GZ_CONFIG_PATH=$(dirname "$sim_yaml"):$GZ_CONFIG_PATH
fi

export RUBYLIB=$(dirname "$cmdgui_rb")${RUBYLIB:+:$RUBYLIB}
if [[ -n "$cmdsim_rb" ]]; then
  export RUBYLIB=$(dirname "$cmdsim_rb"):$RUBYLIB
fi

export GZ_GUI_PLUGIN_PATH=$(dirname "$libgz_gui")${GZ_GUI_PLUGIN_PATH:+:$GZ_GUI_PLUGIN_PATH}

# Qt is built from source: the xcb/offscreen QPA plugins and the QML modules
# gz-gui imports are linked statically into libgz-gui-shared.so, so there is
# no QT_PLUGIN_PATH / QML2_IMPORT_PATH to set up. Prefer xcb, falling back to
# offscreen when no display is available.
export QT_QPA_PLATFORM=${QT_QPA_PLATFORM:-"xcb;offscreen"}

if [[ -n "${RUNFILES_DIR:-}" && -d "${RUNFILES_DIR}/_main/lib" ]]; then
  export GZ_RENDERING_PLUGIN_PATH="${GZ_RENDERING_PLUGIN_PATH:-${RUNFILES_DIR}/_main/lib}"
  export OGRE2_RESOURCE_PATH="${OGRE2_RESOURCE_PATH:-${RUNFILES_DIR}/_main/lib}"
else
  rendersystem_gl3plus=$(find_runfile "ogre-next/RenderSystem_GL3Plus.so" "ogre-next+/RenderSystem_GL3Plus.so" || true)
  if [[ -n "$rendersystem_gl3plus" ]]; then
    export OGRE2_RESOURCE_PATH="${OGRE2_RESOURCE_PATH:-$(dirname "$rendersystem_gl3plus")}"
  fi
fi
if [[ -n "${RUNFILES_DIR:-}" && -d "${RUNFILES_DIR}/_main/share/gz/gz-rendering" ]]; then
  export GZ_RENDERING_RESOURCE_PATH="${GZ_RENDERING_RESOURCE_PATH:-${RUNFILES_DIR}/_main/share/gz/gz-rendering}"
elif [[ -n "${RUNFILES_DIR:-}" && -d "${RUNFILES_DIR}/gz-rendering+/ogre2/src/media" ]]; then
  export GZ_RENDERING_RESOURCE_PATH="${GZ_RENDERING_RESOURCE_PATH:-${RUNFILES_DIR}/gz-rendering+}"
fi

exec ruby "$gz_rb" "$@"
