#!/bin/bash

source algo/bin/activate
cd workspace
tmux new-session -d -s algo 'python main.py'
tmux new_session -d -s algo-web 'python web.py'