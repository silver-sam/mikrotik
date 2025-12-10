#!/bin/bash

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check for virtual environment directory
if [ -d "$DIR/venv" ]; then
    PYTHON_EXEC="$DIR/venv/bin/python"
    if [ ! -f "$PYTHON_EXEC" ]; then
        echo "Error: venv directory exists but python executable not found."
        exit 1
    fi
else
    echo "Warning: No 'venv' directory found. Trying system python3..."
    PYTHON_EXEC="python3"
fi

# Run the script
exec "$PYTHON_EXEC" "$DIR/devices.py" "$@"
