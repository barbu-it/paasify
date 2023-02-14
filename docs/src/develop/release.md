# Build and distribute

This pages explains how to change Paasify version and publish releases.

## Quickstart

There are few operation related to this topic

* Bump version: Increment version and generate changelogs
* Build: Create artifacts, including python packages with changelogs
* publish: Push artifacts onto remote repositories, such as Pypi.org or github release


### Bump version

The bump operation consists in:

1. Generate latest changes files
1. Call `cz` with the `bump` command
    1. Update version in `.cz.toml`
    1. Update version in `pyproject.toml`
    1. Generate `CHANGELOG.md`
    1. Commit changed files and commit
    1. Tag commit with version name


To check what is the next version you would release according your last commits, you can run:

```
$ task version 
task: [version] ./scripts/bump.sh 
INFO: Detecting devel branch
INFO: Dry mode enabled, use with --exec to run changes
INFO: Changelog to be generated:
DEBUG: command: cz bump --changelog --dry-run --prerelease alpha   
bump: version 0.1.0a0 → 0.1.0a1
tag to create: 0.1.0a1

...
```

The output is self explanatory, it shows you what is your next direction. The major/minor/patch depends 
on how you prefixed your commits. Enventually, you can force the context this way:

```
$ task version -- alpha
$ task version -- beta 10
$ task version -- release
```

When you feel agree with the proposed result, you can run it for good, replace `version` to `bump`, from the previous example:

```
$ task bump
$ task bump -- alpha
$ task bump -- beta 10
$ task bump -- release
```


### Build

Build process will build python package with poetry and copy changelogs into the `dist` directory

```
task build
```

### Publish

Artifacts are published on many destinations:

* [pypi.org](https://pypi.org/project/paasify/): Python release
* [Github Project](https://github.com/barbu-it/paasify/): Project sources
* [Github Release](https://github.com/barbu-it/paasify/releases): Github tar.gz release
* [Github Pages](https://barbu-it.github.io/paasify/): Official documentation
* [DockerHub](): Docker image release (TODO)
* [Github Container](): Docker image release (TODO)

To publish:

```
task publish
```

## Implementation details

While designing CI/CD system around paasify development, it has been decided to not depend upon 
third party tools. Every CI/CD commands must be able to be launched via `task`. No github actions or whatever vendor specific tasks, 
everything the CI/CD can do the developer should be able to do so.

Everything should be able to run on the developper workstation.


### CI/CD

There are some github configurations and workflow defined into the `.github` project in the project dir. Because all CI/CD system
is run via task, there is almost no need to configure the CI/CD outside of simply calling `task` commands.


### Bump

The current project allows a smart and easy versionning operation:

* Uses a plugin that allow to guess its version from its package name (see: `pyproject.toml`)
    * No need to update python code to bump version
* `cz` handle version bumping, in our case it will update itself `pyproject.toml`
    * No need to update python `pyproject.toml` to bump version
* A `./scripts/bump.sh` script exist to help developer to determine what should be the next version
    * No need to guess what gonna be named the next version
    * You can still override what gonna be the next version 
* `task` is used as main wrapper
    * For most of case, you can simple alternatce between `task version` and `task bump`


Behind the scene, `task` only call the underline script `bump.sh`, to get more informations:
```
$ ./scripts/bump.sh --help
INFO: Detecting devel branch
  Helps to bump project version according to git status

  Usage: ./scripts/bump.sh [OPTIONS,...]

  OPTIONS:
    alpha,beta,rc         Force version type
    major,minor,patch     Force version type
    INTEGER               Positive number for dev releases

  EXAMPLES:
    ./scripts/bump.sh beta
    ./scripts/bump.sh beta 2
    ./scripts/bump.sh minor alpha 3

```


!!! Warning: Be sure you have at least commited one change before
    If you have not comitted any changes, you should get this error message.
    ```
    No commits found
    task: Failed to run task "version": exit status 3
    ```

### Logo

Paasify official logo is included as a SVG file in the `logo/` directory. They are provided as SVG, so they can 
easily be patched and commited into git with a vectorial editor tool, such as [Inkscape](https://inkscape.org/). An 
helper script is provided to generate favicon:

```
task -t scripts/Taskfile.dev.yml gen_favicon
```

