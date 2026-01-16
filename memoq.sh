#!/bin/bash
# memoQ CLI wrapper script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
"$SCRIPT_DIR/.venv/bin/python" -m memoq_cli.cli "$@"
