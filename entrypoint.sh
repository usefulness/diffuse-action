#!/bin/bash -e

wget "https://github.com/JakeWharton/diffuse/releases/download/$INPUT_VERSION/diffuse-$INPUT_VERSION-binary.jar" -q -O diffuse.jar
chmod +x diffuse.jar
