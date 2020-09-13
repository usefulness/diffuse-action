#!/bin/bash -e

downloadArgs=()
[ "$INPUT_DEBUG" != true ] && downloadArgs+=(-q)

wget "https://github.com/JakeWharton/diffuse/releases/download/$INPUT_VERSION/diffuse-$INPUT_VERSION-binary.jar" "${downloadArgs[@]}" -O diffuse.jar

args=()
if [[ $INPUT_NEW_FILE == *.aab ]]; then
  args+=(--aab)
elif [[ $INPUT_NEW_FILE == *.aar ]]; then
  args+=(--aar)
elif [[ $INPUT_NEW_FILE == *.jar ]]; then
  args+=(--jar)
fi

if [ "${INPUT_DEBUG}" == true ]; then
  echo "Old: $(wc -c "$INPUT_OLD_FILE")"
  echo "New: $(wc -c "$INPUT_NEW_FILE")"
  echo "${args[@]}"
fi

function sanitize() {
  local diff=$1
  diff="${diff//'%'/'%25'}"
  diff="${diff//$'\n'/'%0A'}"
  diff="${diff//$'\r'/'%0D'}"
  echo "$diff"
}

[ "$INPUT_OLD_MAPPING_FILE" ] && args+=(--old-mapping "$INPUT_OLD_MAPPING_FILE")
[ "$INPUT_NEW_MAPPING_FILE" ] && args+=(--new-mapping "$INPUT_NEW_MAPPING_FILE")

diff=$(java -jar diffuse.jar diff "${args[@]}" "$INPUT_OLD_FILE" "$INPUT_NEW_FILE")

textDiff=$(sanitize "$diff")

if [ "${INPUT_DEBUG}" == true ]; then
  echo "Diff size ${#textDiff}"
  echo "Diff $textDiff"
fi
echo "::set-output name=text-diff::$textDiff"
