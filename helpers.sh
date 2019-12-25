#!/bin/bash

#function g(){
#    echo cd /home/amchap06/github/mortgagetvm/mortgagetvm
#    cd /home/amchap06/github/mortgagetvm/mortgagetvm
#}
function c(){
    echo vi app/assets/3_stock.css
    vi app/assets/3_stock.css
}
# helper function to vim app
function v(){
    main=$(switchmain $1)
    echo vi $main
    vi $main
}
function vc(){
    main=$(switchmain $1)
    echo vi -O $main app/assets/3_stock.css
    vi -O $main app/assets/3_stock.css
}
# helper function to vim app
function v(){
    main=$(switchmain $1)
    echo vi $main
    vi $main
}
# helper function to test app
function t(){
    main=$(switchmain $1)
    cp $main app/main.py
    echo cp $main app/main.py
    echo ./t.sh $main
    ./t.sh $main
}
#helper function to set which app we are working on
function switchmain(){
    if [ -z "$1" ]
    then
        selection=$(cat current.txt)
    else
        selection=$1
        echo $selection > current.txt
    fi
    main="app/main${selection}.py" 
    echo $main
    #echo cp $main main.py
    #cp $main main.py
}
