#!/bin/bash

FLASK_APP="app/main.py"

main="app/main.py"
# helper function to open app in vscode
function c(){
    echo code $main
    code $main
}
# helper function to vim app
function v(){
    echo vi $main
    vi $main
}
# helper function to vim css file
function vc(){
    echo vi app/assets/3_stock.css
    vi app/assets/3_stock.css
}
# helper function to vim css file
function cc(){
    echo code app/assets/3_stock.css
    code app/assets/3_stock.css
}
# helper function to test app
function t(){
    echo ./t.sh $main
    ./t.sh $main
}
