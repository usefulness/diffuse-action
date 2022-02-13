#!/usr/bin/python
import os
import re
import subprocess
import requests
import json
from itertools import zip_longest


def find_tool_url():
    lib_version = os.getenv("INPUT_LIB_VERSION", "").strip()
    diffuse_repo = os.getenv("INPUT_DIFFUSE_REPO", "").strip()
    if not diffuse_repo:
        raise RuntimeError("You must provide valid `diffuse-repo` input")
    if not lib_version:
        raise RuntimeError("You must provide valid `lib-version` input")

    if lib_version == "latest":
        response = requests.get(
            "https://api.github.com/repos/{0}/releases/latest".format(diffuse_repo),
            headers={
                "Content-Type": "application/vnd.github.v3+json",
                "Authorization": "token {0}".format(os.getenv("INPUT_GITHUB_TOKEN", ""))
            }
        )

        if is_debug():
            print("X-RateLimit-Limit: {0}".format(response.headers["X-RateLimit-Limit"]))
            print("X-RateLimit-Used: {0}".format(response.headers["X-RateLimit-Used"]))
            print("X-RateLimit-Remaining: {0}".format(response.headers["X-RateLimit-Remaining"]))

        parsed = json.loads(response.content)

        return parsed["assets"][0]["browser_download_url"]
    else:
        return "https://github.com/{0}/releases/download/{1}/diffuse-{1}-binary.jar" \
            .format(diffuse_repo, lib_version)


def is_debug():
    return os.getenv("INPUT_DEBUG", False)


def github_output(message):
    return message.replace("%", "%25") \
        .replace("\n", "%0A") \
        .replace("\r", "%0D") \
        .replace('\x00', '')


def section(_title, _content):
    return f"""
<details>
  <summary>{_title}</summary>
  
\\`\\`\\`
{_content}
\\`\\`\\`
</details>

"""


def header(_content):
    return f"""
\\`\\`\\`
{_content}
\\`\\`\\`
"""


def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def sizeof_fmt(num, suffix='B', sign=False):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            if sign:
                return "%+3.1f%s%s" % (num, unit, suffix)
            else:
                return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    if sign:
        return "%+.1f%s%s" % (num, 'Yi', suffix)
    else:
        return "%.1f%s%s" % (num, 'Yi', suffix)


url = find_tool_url()
if is_debug():
    print("url of the tool: {}".format(url))

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

oldSize = os.stat(oldFile).st_size
oldSizeText = sizeof_fmt(oldSize)
newSize = os.stat(newFile).st_size
newSizeText = sizeof_fmt(newSize)
diff = newSize - oldSize
diffComment1 = f"**{sizeof_fmt(diff, sign=True)}** ({oldSizeText} -> {newSizeText})"
if is_debug():
    print("Old: {} bytes".format(oldSizeText))
    print("New: {} bytes".format(newSizeText))
    print("Diff: {} bytes".format(diffComment1))
    print(diffComment1)
    print(" ".join(java_call))

os.system(f"echo \"::set-output name=size-old-bytes::{oldSize}\"")
os.system(f"echo \"::set-output name=size-old-text::{oldSizeText}\"")
os.system(f"echo \"::set-output name=size-new-bytes::{newSize}\"")
os.system(f"echo \"::set-output name=size-new-text::{newSizeText}\"")
os.system(f"echo \"::set-output name=size-diff-comment_style_1::{diffComment1}\"")

process = subprocess.Popen(java_call, stdout=subprocess.PIPE)
out, _ = process.communicate()

if process.returncode != 0:
    raise Exception("Error while executing diffuse")

diff = out.decode("utf-8").strip()

if is_debug():
    print(f"Diff size: {len(diff)}")

headerPattern = re.compile('=+\\s=+\\s+(\\w+)\\s+=+\\s=*\\s')
sections = ["SUMMARY"] + headerPattern.split(diff)

if is_debug():
    print(f"Found {len(sections)} sections")

github_comment = ""
github_comment_all_collapsed = ""
github_comment_no_dex = ""
github_comment_no_dex_all_collapsed = ""
github_output_limit = 4500

for (title, content) in grouper(sections, 2):
    key = title.lower().strip().replace(" ", "-")
    value = content.rstrip().lstrip("\n").replace("$", "_")
    if len(value) > github_output_limit:
        value = value[0:github_output_limit] + "\n...✂"

    os.system("echo \"::set-output name={}::{}\"".format(key, github_output(value)))
    if key == "summary":
        github_comment += header(value)
        github_comment_no_dex += header(value)
        github_comment_all_collapsed += section(title, value)
        github_comment_no_dex_all_collapsed += section(title, value)
    else:
        github_comment += section(title.strip(), value)
        github_comment_all_collapsed += section(title.strip(), value)
        if key != "dex":
            github_comment_no_dex += section(title.strip(), value)
            github_comment_no_dex_all_collapsed += section(title.strip(), value)

output = open("diffuse-output.txt", "w")
output.write(diff)
output.close()
outputPath = os.path.realpath(output.name)
if is_debug():
    print(f"Full output stored in: {outputPath}")
os.system(f"echo \"::set-output name=diff-file::{outputPath}\"")
os.system(f"echo \"::set-output name=diff-raw::{github_output(diff[0:github_output_limit])}\"")
os.system(f"echo \"::set-output name=diff-gh-comment::{github_output(github_comment)}\"")
os.system(f"echo \"::set-output name=diff-gh-comment-all-collapsed::{github_output(github_comment_all_collapsed)}\"")
os.system(f"echo \"::set-output name=diff-gh-comment-no-dex::{github_output(github_comment_no_dex)}\"")
os.system(
    f"echo \"::set-output name=diff-gh-comment-no-dex-all-collapsed::{github_output(github_comment_no_dex_all_collapsed)}\"")
