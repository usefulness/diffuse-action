#!/usr/bin/python
import os
import re
import subprocess
import requests
import json
import uuid
import zipfile
import stat
from itertools import zip_longest


def find_tool_coordinates():
    input_lib_version = os.getenv("INPUT_LIB_VERSION", "").strip()
    diffuse_repo = os.getenv("INPUT_DIFFUSE_REPO", "").strip()
    if not diffuse_repo:
        raise RuntimeError("You must provide valid `diffuse-repo` input")
    if not input_lib_version:
        raise RuntimeError("You must provide valid `lib-version` input")

    if input_lib_version == "latest":
        request_url = "https://api.github.com/repos/{0}/releases/latest".format(diffuse_repo)
    else:
        request_url = "https://api.github.com/repos/{0}/releases/tags/{1}".format(diffuse_repo, input_lib_version)

    response = requests.get(
        request_url,
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

    return parsed["assets"][0]["browser_download_url"], parsed["tag_name"]


def is_debug():
    return os.getenv("INPUT_DEBUG", False)


def is_windows():
    return os.name == "nt"


def github_output(key, message):
    delimiter = str(uuid.uuid4())
    with open(os.environ['GITHUB_OUTPUT'], mode='a', encoding='UTF-8') as fh:
        print(f'{key}<<${delimiter}', file=fh)
        print(message, file=fh)
        print(f'${delimiter}', file=fh)


def section(_title, _content):
    return f"""
<details>
  <summary>{_title}</summary>
  
```
{_content}
```
</details>

"""


def header(_content):
    return f"""
```
{_content}
```
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


url, lib_version = find_tool_coordinates()
if is_debug():
    print("url of the tool: {}".format(url))

downloadArgs = ""
if not is_debug():
    downloadArgs += "-q"

if url.endswith(".jar"):
    r = requests.get(url, allow_redirects=True)
    open("diffuse.jar", "wb").write(r.content)
    exec_call = ["java", "-jar", "diffuse.jar"]
else:
    r = requests.get(url, allow_redirects=True)
    open("diffuse.zip", "wb").write(r.content)
    with zipfile.ZipFile("diffuse.zip", "r") as zip_ref:
        zip_ref.extractall("diffuse_extracted")

    if is_windows():
        executable_name = "diffuse.bat"
    else:
        executable_name = "diffuse"
    runnable = os.path.join("diffuse_extracted", f"diffuse-{lib_version}", "bin", executable_name)
    st = os.stat("diffuse_extracted")
    os.chmod(runnable, st.st_mode | stat.S_IEXEC)
    exec_call = [runnable]
exec_call.append("diff")

oldFile = os.getenv("INPUT_OLD_FILE")
newFile = os.getenv("INPUT_NEW_FILE")

typeSelector = {
    ".apk": "--apk",
    ".aab": "--aab",
    ".aar": "--aar",
    ".jar": "--jar",
}
path, file_extension = os.path.splitext(newFile)
exec_call.append(typeSelector.get(file_extension))
exec_call.append(oldFile)
exec_call.append(newFile)

if os.getenv("INPUT_OLD_MAPPING_FILE").strip():
    exec_call.extend(["--old-mapping", os.getenv("INPUT_OLD_MAPPING_FILE")])
if os.getenv("INPUT_NEW_MAPPING_FILE").strip():
    exec_call.extend(["--new-mapping", os.getenv("INPUT_NEW_MAPPING_FILE")])
exec_call.append("--text")
output_file_name = "diffuse-output.txt"
exec_call.append(output_file_name)

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
    print(" ".join(exec_call))

github_output("size-old-bytes", oldSize)
github_output("size-old-text", oldSizeText)
github_output("size-new-bytes", newSize)
github_output("size-new-text", newSizeText)
github_output("size-diff-comment_style_1", diffComment1)


process = subprocess.run(exec_call)
if process.returncode != 0:
    raise Exception("Error while executing diffuse")

with open(output_file_name, mode="r", encoding="utf-8") as output:
    outputPath = os.path.realpath(output.name)
    diff = output.read()

if process.returncode != 0:
    raise Exception("Error while executing diffuse")

if is_debug():
    print(f"Diff size: {len(diff)}")

headerPattern = re.compile('=+\\s=+\\s+(\\w+)\\s+=+\\s=*\\s')
sections = ["SUMMARY"] + headerPattern.split(diff)

if is_debug():
    print(f"Found {len(sections)} sections")
    print(f"Full output stored in: {outputPath}")

github_comment = ""
github_comment_all_collapsed = ""
github_comment_no_dex = ""
github_comment_no_dex_all_collapsed = ""
github_output_limit = 4500

for (title, content) in grouper(sections, 2):
    key = title.lower().strip().replace(" ", "-")
    value = content.rstrip().lstrip("\n").replace("$", "_").replace("`", "")
    if len(value) > github_output_limit:
        value = value[0:github_output_limit] + "\n...✂"

    github_output(key, value)
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

github_output("diff-file", outputPath)
github_output("diff-raw", diff[0:github_output_limit])
github_output("diff-gh-comment", github_comment)
github_output("diff-gh-comment-all-collapsed", github_comment_all_collapsed)
github_output("diff-gh-comment-no-dex", github_comment_no_dex)
github_output("diff-gh-comment-no-dex-all-collapsed", github_comment_no_dex_all_collapsed)
