#!/usr/bin/env bash
set -euo pipefail

# Train the model and run both action server and rasa shell.
# You may run action server and rasa shell in separate terminals if preferred.

VENV_DIR=".venv"
if [ -d "$VENV_DIR" ]; then
  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate"
fi

# Train
rasa train

# Start action server in background terminal if tmux/screen exists, otherwise instruct user.
# Default approach: run both in foreground one by one for portability.

# Start actions (in a separate process if user manually runs it). Here we start it first.
( rasa run actions --port 5055 --cors "*" & )

# Then run interactive shell
rasa shell --debug
