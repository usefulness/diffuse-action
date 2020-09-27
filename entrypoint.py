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


url = "https://github.com/JakeWharton/diffuse/releases/download/{0}/diffuse-{0}-binary.jar" \
    .format(os.getenv("INPUT_VERSION"))
downloadArgs = ""
if is_debug():
    downloadArgs = "-q"
os.system("wget \"{}\" {} -O diffuse.jar".format(url, downloadArgs))

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
    print("Diff size: {}".format(len(diff)))

pattern = re.compile('(=+\\s=+\\s+(?P<title>\\w+)\\s+=+\\s=*\\s)?(?P<content>[^=]+)')

for match in pattern.finditer(diff):
    title = (match.group("title") or "Summary").lower().strip().replace(" ", "-")
    content = match.group("content").strip()
    os.system("echo \"::set-output name={}::{}\"".format(title, github_output(content)))
    if is_debug():
        print("{} size: {}".format(title, len(content)))

output = open("diffuse-output.txt", "w")
output.write(diff)
output.close()
os.system("echo \"::set-output name=file-diff::{}\"".format(os.path.realpath(output.name)))
os.system("echo \"::set-output name=text-diff::{}\"".format(github_output(diff)))
