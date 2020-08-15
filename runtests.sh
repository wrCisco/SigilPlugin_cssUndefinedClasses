#!/usr/bin/env sh

script_dir="$(cd "$(dirname "$0")" && pwd)"

if [ -d /usr/local/share/sigil/plugin_launchers/python ]; then
  # Sigil built from source with standard path on Linux
  Sigil_plugin_launchers=/usr/local/share/sigil/plugin_launchers/python
elif [ -d /usr/share/sigil/plugin_launchers/python ]; then
  # Sigil installed from Arch repos
  Sigil_plugin_launchers=/usr/share/sigil/plugin_launchers/python
fi
PYTHONPATH="${script_dir}"/cssUndefinedClasses:${Sigil_plugin_launchers}:${PYTHONPATH}
export PYTHONPATH

if [ -z "$SigilGumboLibPath" ] ; then
  if [ -f /usr/local/lib/sigil/libsigilgumbo.so ]; then
    # Sigil built from source with standard path on Linux
    export SigilGumboLibPath=/usr/local/lib/sigil/libsigilgumbo.so
  elif [ -f /usr/lib/sigil/libsigilgumbo.so ]; then
    # Sigil installed from Arch repos
    export SigilGumboLibPath=/usr/lib/sigil/libsigilgumbo.so
  fi
fi


python -m unittest discover -s "${script_dir}/tests" "$@"
