#!/usr/bin/python
import os
import re
import subprocess


def is_debug():
    return os.getenv("INPUT_DEBUG", False)


def github_output(message: str):
    return message.replace("%", "%25") \
        .replace("\n", "%0A") \
        .replace("\r", "%0D") \
        .replace('\x00', '')


def section(_title: str, _content: str):
    return f"""
<details>
  <summary>{_title}</summary>
  
\\`\\`\\`
  {_content}
\\`\\`\\`
</details>

"""


url = "https://github.com/JakeWharton/diffuse/releases/download/{0}/diffuse-{0}-binary.jar" \
    .format(os.getenv("INPUT_VERSION"))
downloadArgs = ""
if not is_debug():
    downloadArgs += "-q"
os.system(f"wget \"{url}\" {downloadArgs} -O diffuse.jar")

java_call = ["java", "-jar", "diffuse.jar", "diff"]

oldFile = os.getenv("INPUT_OLD_FILE")
newFile = os.getenv("INPUT_NEW_FILE")

typeSelector = {
    ".apk": "--apk",
    ".aab": "--aab",
    ".aar": "--aar",
    ".jar": "--jar",
}
path, file_extension = os.path.splitext(newFile)
java_call.append(typeSelector.get(file_extension))
java_call.append(oldFile)
java_call.append(newFile)

if os.getenv("INPUT_OLD_MAPPING_FILE").strip():
    java_call.extend(["--old-mapping", os.getenv("INPUT_OLD_MAPPING_FILE")])
if os.getenv("INPUT_NEW_MAPPING_FILE").strip():
    java_call.extend(["--new-mapping", os.getenv("INPUT_NEW_MAPPING_FILE")])

if is_debug():
    print("Old: {} bytes".format(os.stat(oldFile).st_size))
    print("New: {} bytes".format(os.stat(newFile).st_size))
    print(" ".join(java_call))

process = subprocess.Popen(java_call, stdout=subprocess.PIPE)
out, _ = process.communicate()

if process.returncode != 0:
    raise Exception("Error while executing diffuse")

diff = out.decode("utf-8").strip()

if is_debug():
    print(f"Diff size: {len(diff)}")

pattern = re.compile('(=+\\s=+\\s+(?P<title>\\w+)\\s+=+\\s=*\\s)?(?P<content>[^=]+)')

diffDictionary = {}
for match in pattern.finditer(diff):
    title = (match.group("title") or "Summary").lower().strip().replace(" ", "-")
    content = match.group("content").strip().replace("$", "\\$")
    diffDictionary[title] = content

output = open("diffuse-output.txt", "w")
output.write(diff)
output.close()
outputPath = os.path.realpath(output.name)
if is_debug():
    print(f"Full output stored in: {outputPath}")
os.system(f"echo \"::set-output name=diff-file::{outputPath}\"")
os.system(f"echo \"::set-output name=diff-raw::{github_output(diff)}\"")

github_comment = ""
if diffDictionary["summary"]:
    github_comment += f"""
\\`\\`\\`
{diffDictionary["summary"].strip()}
\\`\\`\\`
"""

for key, value in diffDictionary.items():
    os.system("echo \"::set-output name={}::{}\"".format(key, github_output(value)))
    if len(value.strip()) > 0 and key != "summary":
        github_comment += section(key, value)

os.system(f"echo \"::set-output name=diff-gh-comment::{github_output(github_comment)}\"")
