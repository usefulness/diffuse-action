#!/bin/bash -e

wget "https://github.com/JakeWharton/diffuse/releases/download/$INPUT_VERSION/diffuse-$INPUT_VERSION-binary.jar" -O diffuse.jar
ls -l
chmod +x diffuse.jar

args=()
diff=$(diffuse.jar "${args[@]}" "$INPUT_FILE" "$INPUT_FILE")
diff="${diff//'%'/'%25'}"
diff="${diff//$'\n'/'%0A'}"
diff="${diff//$'\r'/'%0D'}"
echo "::set-output name=text-diff::$diff"
