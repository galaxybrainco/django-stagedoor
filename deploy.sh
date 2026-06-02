#! /bin/sh
# Use `uv publish` for PyPI publishing with trusted publishing.
# Make sure you have PyPI trusted publishing configured for this repo.
# See: https://docs.pypi.org/trusted-publishers/

set -e

rm -rf dist/
uv build
uv publish
