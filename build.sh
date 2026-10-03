#!/usr/bin/env bash
# Build dist/AlgorithmStudy with PyInstaller (macOS / Linux). Windows: use build.bat.
set -euo pipefail
cd "$(dirname "$0")"

echo "=== Algorithm Study - build ==="
PY=.venv/bin/python
if [ ! -x "$PY" ]; then
  echo "Creating a virtual environment in .venv ..."
  python3 -m venv .venv
fi
"$PY" --version

if ! "$PY" -c "import flask, sympy, waitress, dotenv, PyInstaller" 2>/dev/null; then
  echo "Installing build dependencies from requirements-build.txt ..."
  "$PY" -m pip install --disable-pip-version-check -r requirements-build.txt
fi
"$PY" -c "import flask, sympy, waitress, dotenv, PyInstaller; print('Dependencies OK - PyInstaller', PyInstaller.__version__)"

rm -rf build dist
echo "Building - this takes a minute or two ..."
"$PY" -m PyInstaller --noconfirm --clean AlgorithmStudy.spec

if [ ! -f dist/AlgorithmStudy ]; then
  echo "=== Build FAILED: dist/AlgorithmStudy was not created ===" >&2
  exit 1
fi
echo
echo "=== Build succeeded ==="
echo "Executable: $(pwd)/dist/AlgorithmStudy"
