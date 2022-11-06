# Developpement


This is the general workflow:

1. Code Development
    * Update the code
    * Update the tests
    * Update the doc
    * Update release
        * Generate release notes
2. Documentation:
    * Generate jsonschema documentation
    * Generate mkdocs:
        * Include other files of the project
        * Import jsonschema documentation
        * Generate python code reference
3. Code Quality:
    * Run autolinter `black`
    * Run linting report `pylint`
    * Run tests:
        * Run unit tests
        * Run code-coverage
        * Run functional tests
        * Run examples tests
4. Delivery:
    * Documentation:
        * Build static documentation
    * Release Pypi:
        * Build package
        * Push package
    * Release Container:
        * Build Docker Build env
        * Build Paasify App Image
        * Build Paasify Documentation Image
        * Push images
5. Contributing:
    * Create a git commit
    * Create a pull request
    * Review of the commit
    * Merge to upstream if accepted

Once you developped or changed things, you need to test

## Recommended tools

Recommended tools:

* [Poetry](https://python-poetry.org/): Python project management
* [Task](https://taskfile.dev/): MakeFile replacement
* [direnv](https://direnv.net/): Allow to enable

Troubleshooting:

* [jq](https://stedolan.github.io/jq/): Process JSON files
* [yq](https://mikefarah.gitbook.io/yq/): Process YAML files


## Quickstart for development

Project setup:
```
git clone --recurse-submodules ... paasify
cd paasify
pre-commit install --install-hook  --hook-type commit-msg --hook-type pre-push
```

The main steps as been implemented as task files.
```
$ task --list
```

### Documentation

You can manually edit the documentation or simply
use the integrated web IDE.
```
task doc:serve_ide
```

Applications:

* Documentation: [http://127.0.0.1:8042](http://127.0.0.1:8042/)
* Jupyter Notebook Editor:  [http://127.0.0.1:8043](http://127.0.0.1:8043/), token is shown in docker logs.
* Code Editor (optional):  [http://127.0.0.1:8044](http://127.0.0.1:8044/)

From these, you can both edit the code with a visual editor and also
run jupyter notebooks, and see in live the result in the web page.

### Development

Run code linting:
```
task run_qa
```

Run tests:
```
task run_tests
```

Build docuementation:
```
task doc:build_doc
```

Build docker image:
```
task docker_build_image
```

Build python package:
```
task pkg_build
```

### Test and Review

Try directly:
```
paasify --version
```

Try you current code version in docker:
```
task docker_run -- --version
```

Try package installation:
```
pip3 install dist/paasify-0.1.1a2.tar.gz
```

Show documentation:
```
task doc:serve_doc:
```

Test dockerized paasify with your project:
```
alias paasify-docker='docker run -ti --rm -v $(dirname $PWD):/work -w /work/$(basename $PWD) paasify:latest paasify'

# Run command from outside
paasify-docker info

# To get into your project
docker run -ti --rm -v $(dirname $PWD):/work -w /work/$(basename $PWD) bash
```


### Commit reviewable code

Bumping versions workflow:
```
poetry version prepatch  # Idempotent
poetry version prerelease
poetry version patch
poetry version minor
poetry version major

# Reset version
poetry version <expected version>

# Reset to default git version
task
git checkout paasify.version.py
poetry version $(python -m paasify.version)

```

Create commit:
```
git add <modified files>
git commit -m ""
```

### Release

TODO

## Commit message standards

TODO:
