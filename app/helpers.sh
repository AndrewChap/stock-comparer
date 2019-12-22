#!/bin/bash

function g(){
    echo cd /home/amchap06/github/mortgagetvm/mortgagetvm
    cd /home/amchap06/github/mortgagetvm/mortgagetvm
}
function c(){
    echo vi assets/3_mort.css
    vi assets/3_mort.css
}
# helper function to vim app
function v(){
    main=$(s $1)
    echo vi $main
    vi $main
}
# helper function to test app
function t(){
    main=$(s $1)
    $cp $main main.py
    $echo $main main.py
    echo ./t.sh $main
    ./t.sh $main
}
#helper function to set which app we are working on
function s(){
    if [ -z "$1" ]
    then
        selection=$(cat current.txt)
    else
        selection=$1
        echo $selection > current.txt
    fi
    main=main${selection}.py 
    echo $main
    #echo cp $main main.py
    #cp $main main.py
}

