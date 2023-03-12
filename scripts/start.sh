#!/bin/bash

source workspace/algo/bin/activate
cd workspace/hippo-trade-aws
tmux new -s algo 'python main.py'
tmux new -s algo-web 'python web.py'