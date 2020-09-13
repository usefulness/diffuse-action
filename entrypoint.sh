#!/bin/bash -e

downloadArgs=()
[ "$INPUT_DEBUG" != true ] && downloadArgs+=(-q)

wget "https://github.com/JakeWharton/diffuse/releases/download/$INPUT_VERSION/diffuse-$INPUT_VERSION-binary.jar" "${downloadArgs[@]}" -O diffuse.jar

[ "$INPUT_DEBUG" == true ] && ls -l
python3 parser.py
