#!/bin/bash

# This should get rid of any previous dash apps running so the port can be cleared
pkill -9 -f python3

# launch dash app
echo python3 $1
python3 $1
#python3 main.py
