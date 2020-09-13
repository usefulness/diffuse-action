#!/usr/bin/python
import os
import subprocess


def is_debug():
    return os.getenv("INPUT_DEBUG", True)


def github_output(message: str):
    return message.replace("%", "%25") \
        .replace("\n", "%0A") \
        .replace("\r", "%0D")


java_call = ["java", "-jar", "diffuse.jar", "diff"]

oldFile = os.getenv("INPUT_OLD_FILE")
newFile = os.getenv("INPUT_NEW_FILE")

typeSelector = {
    ".apk": "--apk",
    ".aab": "--aab",
    ".aar": "--aar",
    ".jar": "--jar",
}
path, file_extension = os.path.splitext(oldFile)
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
    print("Diff\n{}".format(diff))

lines = diff.split("\n")
divider = next((index for index, line in enumerate(lines) if "=================" in line), None)

summary = None

if divider:
    summary = lines[0:divider - 1]
else:
    summary = lines

summary = "\n".join(summary or []).strip()

os.system("echo \"::set-output name=text-diff::{}\"".format(github_output(diff)))
os.system("echo \"::set-output name=summary::{}\"".format(github_output(summary)))

if is_debug():
    print("SUMMARY:\n{}".format(summary))
