#!/bin/bash

nix-shell --run 'python strategy_optimizer/src/main.py --mode paper > application.log 2>&1' &
nix-shell --run 'cd strategy_optimizer && python view_dashboard.py' &
