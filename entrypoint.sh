#!/bin/bash -e

wget "https://github.com/JakeWharton/diffuse/releases/download/$INPUT_VERSION/diffuse-$INPUT_VERSION-binary.jar" -q -O diffuse.jar

args=()
diff=$(java -jar diffuse.jar diff "${args[@]}" "$INPUT_FILE" "$INPUT_FILE")
diff=$(java -jar diffuse.jar info "${args[@]}" "$INPUT_FILE")
diff="${diff//'%'/'%25'}"
diff="${diff//$'\n'/'%0A'}"
diff="${diff//$'\r'/'%0D'}"
echo "Dupa $diff"
echo "::set-output name=text-diff::$diff"
