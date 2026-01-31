#!/bin/bash

# Start the main application with the web dashboard
# The web dashboard is now integrated into the main application
nix-shell --run 'python strategy_optimizer/src/main.py --mode paper > application.log 2>&1'
