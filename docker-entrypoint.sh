#!/bin/bash
set -e

# ============================================
# UI-CLI Docker Entrypoint
# Gorilla Powered! 🦍
# ============================================

# If no arguments provided, show help
if [ $# -eq 0 ]; then
    exec ui --help
fi

# If first argument is "shell", start interactive bash
if [ "$1" = "shell" ]; then
    exec /bin/bash
fi

# If first argument is "ui" or starts with "-", pass to ui command
if [ "$1" = "ui" ]; then
    shift
    exec ui "$@"
fi

# Otherwise, pass all arguments to ui command
exec ui "$@"
