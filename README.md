# Diffuse - Github Action
![.github/workflows/after_merge.yml](https://github.com/usefulness/diffuse_action/workflows/.github/workflows/after_merge.yml/badge.svg)

Simple Github Action wrapper for Jake Wharton's [Diffuse](https://github.com/JakeWharton/diffuse) tool.

## Usage 
The action only exposes _output_ containing the diff, so to effectively consume its output it is highly recommended to use other Github Actions to customize your experience.

The work

### Usage:

```
  - id: diffuse
    uses: usefulness/diffuse-action@v1
    with:
      old-file-path: old/file/path/old_file.apk
      new-file-path: new/file/path/new_file.apk
      lib-version: 0.1.0
```

##### Parameters
`old-file-path` - Path to reference file the diff should be generated for  
`new-file-path` - Path to current file the diff should be generated for  
`lib-version` _(Optional)_ - Overrides [Diffuse](https://github.com/JakeWharton/diffuse) dependency version  
`fork-version` _(Optional)_ - Uses [Diffuse](https://github.com/usefulness/diffuse) fork with a fiven version

### Sample: Create Pull Request comment

TODO: explain why to use actions/cache for now and its limitation

1. Integrate with a regular Pull Request workflow:

```yaml
name: Pull Request workflow

on:
  pull_request:

jobs:
  generate-diff:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: set up JDK
      uses: actions/setup-java@v2
      with:
        distribution: 'zulu'
        java-version: 16
      
    - name: Build the apk
      uses: gradle/gradle-build-action@v1
      with:
        arguments: assembleDebug
        dependencies-cache-enabled: true

    # Generating the diff starts here 👇 

    - uses: actions/cache@v2
      name: Download base
      with:
        path: diffuse-source-file
        key: diffuse-${{ github.event.pull_request.base.sha }}

    - id: diffuse
      uses: usefulness/diffuse-action@v1
      with:
        old-file-path: diffuse-source-file
        new-file-path: app/build/outputs/release/app.apk


    # Consuming action output starts here 👇

    - uses: peter-evans/find-comment@v1
      id: find_comment
      with:
        issue-number: ${{ github.event.pull_request.number }}
        body-includes: Diffuse output

    - uses: peter-evans/create-or-update-comment@v1
      if: ${{ steps.diffuse.outputs.diff-raw != null || steps.find_comment.outputs.comment-id != null }}
      with:
        body: |
          Diffuse output (customize your message here): 

          ${{ steps.diffuse.outputs.diff-gh-comment }}
        edit-mode: replace
        comment-id: ${{ steps.find_comment.outputs.comment-id }}
        issue-number: ${{ github.event.pull_request.number }}
        token: ${{ secrets.GITHUB_TOKEN }}

    - uses: actions/upload-artifact@v2
      with:
        name: diffuse-output
        path: ${{ steps.diffuse.outputs.diff-file }}
```

2. Integrate with you post-merge flow:
```yaml
on:
  push:
    branches:
      - master
      - main
      - trunk
      - develop
      - maine
      - mane

jobs:
  diffuse_cache:
    runs-on: ubuntu-latest
    name: Cache artifact for diffuse
    steps:
      - uses: actions/checkout@v2
      
      - name: set up JDK
        uses: actions/setup-java@v2
        with:
          distribution: 'zulu'
          java-version: 16
          
      - name: Build the app
        uses: gradle/gradle-build-action@v1
        with:
          arguments: assembleDebug
          dependencies-cache-enabled: true

      # Integration starts here 👇 
      
      - uses: actions/cache@v2
        name: Upload base
        with:
          path: diffuse-source-file
          key: diffuse-${{ github.sha }}

      # Copy your build artifact under `diffuse-source-file` name which will be saved in cache
      - run: cp sample-apk.apk diffuse-source-file 
        shell: bash

``` 


### More samples

Sample application as a [pull request comment](https://github.com/mateuszkwiecinski/github_browser/pull/52)  
Corresponding [workflow](https://github.com/mateuszkwiecinski/github_browser/blob/master/.github/workflows/run_diffuse.yml) file  

![pull_request](/images/pull_request.png)



<details><summary></summary>
<p>

🙏 Praise 🙏 be 🙏 to 🙏 Wharton 🙏

</p>
</details>
