#!/bin/bash

# Start the main application in the background
nix-shell --run 'python strategy_optimizer/src/main.py --mode paper > application.log 2>&1' &

# Wait for the server to start
sleep 5

URL="http://localhost:5000"

# Function to open URL
open_url() {
  if command -v xdg-open &> /dev/null; then
    xdg-open "$1"
  elif command -v gnome-open &> /dev/null; then
    gnome-open "$1"
  elif command -v open &> /dev/null; then # For macOS
    open "$1"
  else
    echo "Could not automatically open browser. Please open this URL: $1"
  fi
}

open_url "$URL"
