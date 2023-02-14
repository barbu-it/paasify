# Overview

Here is available a list of project references.

## Dependencies

List of Paasify dependencies:

* Paasify runtime dependencies:
    * [Python 3.8+](https://www.python.org/): Recent version of Python
    * [Docker](https://docker.com): Docker
* Paasify python dependencies
    * `Typer`: Command line handling
    * `jsonnet`: Jsonnet parsing
    * `sh`: Easy library to execute shell commands
    * `jsonschema`: handle jsonscheme specs
    * `anyconfig`: load any configs
* Developper dependencies
    * System dependencies:
        * [bash 5](https://www.gnu.org/software/bash/): Recent version of bash5+
        * [git](https://git-scm.com/): Git is a version control system
        * [virtualenv](https://docs.python.org/3/tutorial/venv.html): Manage python virtual env
        * Linux binaries: `curl`, `sed`, `wget` ...
    * Project external dependencies:
        * [Poetry](https://python-poetry.org/): Modern Python project management
        * [Task](https://taskfile.dev/): MakeFile replacement, useful to run tests, qa or to release.
        * [gh](https://cli.github.com/): github client
        * [direnv](https://direnv.net/)`: shell environment manager (optional)
    * Development:
        * `commitizen`: ensure commit respect standards
        * `pytest`: test the code is not broken
        * `pylint`: test the code is always first quality
        * `black`: test the code is always perfectly formatted
        * `pre-commit`: prevent you to commit too early
    * Documentation: (optional)
        * `mkdocs`: Project documentation website
        * `mike`: manage many version of mkdocs
        * `jupyter`: generate docs from commands

Most of these dependencies are handled byt the `scripts/bootstrap_deps.sh` script, please check [setup](install.md) for more details.

## Workflow

Each commit should ideally contains:

1. code
1. tests
1. related documentation
2. valid commit message

This is the general workflow:

1. Code Development
    * Update code
    * Update tests
    * Update related documentation
    * Update docker image

2. Documentation:
    * Update documentation
    * Generate mkdocs:
        * Include other files of the project
        * Import jsonschema documentation
        * Generate python code reference

3. Contributing:
    * Code Quality:
        * Run autolinter `black`
        * Run linting report `pylint`
        * Run tests:
            * Run unit tests
            * Run code-coverage
            * Run functional tests
            * Run examples tests
    * Contribution
        * Create a git commit with relevant git message
        * Create a pull request
        * Review of the commit
        * Merge to upstream if accepted

5. Publish: (Maintainer on main branch only)
    * Bump version
        * Generate release notes
    * Build
        * Pip package
        * Docker image
        * mkdoc documentation
    * Publish
        * Pypi package
        * Github package
        * Documentataion on Github Pages
        * Docker image on github and dockerhub


Once you developed or changed things, you need to start over from the top. Publishing is reserved to the project maintainer.
