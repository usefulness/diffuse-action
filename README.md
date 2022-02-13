# Diffuse - Github Action
![.github/workflows/after_merge.yml](https://github.com/usefulness/diffuse_action/workflows/.github/workflows/after_merge.yml/badge.svg)

Simple Github Action wrapper for Jake Wharton's [Diffuse](https://github.com/JakeWharton/diffuse) tool.

## Usage
The action only exposes _output_ containing the diff, so to effectively consume its output it is highly recommended to use other Github Actions to customize your experience.

### Configuration:
By default, this action uses Diffuse fork - https://github.com/usefulness/diffuse (due to: https://github.com/JakeWharton/diffuse/issues/111)
```
  - id: diffuse
    uses: usefulness/diffuse-action@v1
    with:
      old-file-path: old/file/path/old_file.apk
      new-file-path: new/file/path/new_file.apk
```

You can override the config to use the original [Diffuse](https://github.com/JakeWharton/diffuse) binary
```
  - id: diffuse
    uses: usefulness/diffuse-action@v1
    with:
      old-file-path: old/file/path/old_file.apk
      new-file-path: new/file/path/new_file.apk
      diffuse-repo: JakeWharton/diffuse
      lib-version: 0.1.0
```

##### Parameters
`old-file-path` - Path to reference file the diff should be generated for  
`new-file-path` - Path to current file the diff should be generated for  
`lib-version` _(Optional)_ - Overrides dependency version, by default uses the latest published version  
`diffuse-repo` _(Optional)_ - Overrides [usefulness/diffuse](https://github.com/usefulness/diffuse) as the default repository containing published release artifacts.   

##### Outputs
See full list of [outputs](https://github.com/usefulness/diffuse-action/blob/master/action.yml#L27).  
For example: referencing `steps.diffuse.outputs.diff-gh-comment` at a later stage will print Diffuse tool output as a nicely formatted github comment

### Sample: Create Pull Request comment

TODO: explain why to use free `actions/cache` for now and list its limitation.  
Good introduction to the problem: https://github.com/JakeWharton/dependency-tree-diff/discussions/8#discussioncomment-1535744

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
    
    - uses: actions/setup-java@v2
      with:
        distribution: 'temurin'
        java-version: 17
      
    - uses: gradle/gradle-build-action@v2
      with:
        arguments: assemble

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
  schedule:
    - cron: '0 3 * * 1,4'

jobs:
  diffuse_cache:
    runs-on: ubuntu-latest
    name: Cache artifact for diffuse
    steps:
      - uses: actions/checkout@v2
      
      - uses: actions/setup-java@v2
        with:
          distribution: 'temurin'
          java-version: 17
          
      - uses: gradle/gradle-build-action@v2
        with:
          arguments: assemble

      # Integration starts here 👇 
      
      - uses: actions/cache@v2
        name: Upload base
        with:
          path: diffuse-source-file
          key: diffuse-${{ github.sha }}

      # Copy your build artifact under `diffuse-source-file` name which will be saved in cache
      - run: cp /app/build/outputs/debug/sample-apk.apk diffuse-source-file 
        shell: bash
``` 


### More examples

Sample application as a [pull request comment](https://github.com/mateuszkwiecinski/github_browser/pull/52)  
Corresponding [workflow](https://github.com/mateuszkwiecinski/github_browser/blob/master/.github/workflows/run_diffuse.yml) file  

![pull_request](/images/pull_request.png)



<details><summary></summary>
<p>

🙏 Praise 🙏 be 🙏 to 🙏 Wharton 🙏

</p>
</details>
