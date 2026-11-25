#!/usr/bin/env sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3.7+ não foi encontrado. Instale o Python 3 e tente novamente." >&2
  exit 127
fi
exec python3 "$SCRIPT_DIR/run_filmcraft_web.py" "$@"
