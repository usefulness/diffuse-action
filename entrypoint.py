#!/usr/bin/python
import os
import re
import subprocess
from itertools import zip_longest


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


def header(_content: str):
    return f"""
\\`\\`\\`
  {_content}
\\`\\`\\`
"""


def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


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

headerPattern = re.compile('=+\\s=+\\s+(\\w+)\\s+=+\\s=*\\s')
sections = ["Summary"] + headerPattern.split(diff)

if is_debug():
    print(f"Found {len(sections)} sections")

github_comment = ""
github_comment_no_dex = ""
github_output_limit = 4500

for (title, content) in grouper(sections, 2):
    key = title.lower().strip().replace(" ", "-")
    value = content.strip().replace("$", "_")
    if len(value) > github_output_limit:
        value = value[0:github_output_limit] + "\n...✂"

    os.system("echo \"::set-output name={}::{}\"".format(key, github_output(value)))
    if key == "summary":
        github_comment += header(value)
        github_comment_no_dex += header(value)
    else:
        github_comment += section(title.strip(), value)
        if key != "dex":
            github_comment_no_dex += section(title.strip(), value)

output = open("diffuse-output.txt", "w")
output.write(diff)
output.close()
outputPath = os.path.realpath(output.name)
if is_debug():
    print(f"Full output stored in: {outputPath}")
os.system(f"echo \"::set-output name=diff-file::{outputPath}\"")
os.system(f"echo \"::set-output name=diff-raw::{github_output(diff[0:github_output_limit])}\"")
os.system(f"echo \"::set-output name=diff-gh-comment::{github_output(github_comment)}\"")
os.system(f"echo \"::set-output name=diff-gh-comment-no-dex::{github_output(github_comment_no_dex)}\"")
