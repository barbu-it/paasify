# Update Paasify

This is a quite complete description of the project developer operations. Obviously, most of those tasks are designed to be run inside a CI/CD

!!! warning
    The code is still at beta stage, API may change without prior notice.


## Quickstart


You can directly call it if you are in you virtual env:
```
paasify --version
```

You can try package installation:
```
poetry build
pip3 install dist/paasify-0.1.1a2.tar.gz
```

Show live documentation while you edit files:
```
task doc:serve_doc
```


## Code Development Worklow

Don't feel bad about it, all commands are idempotent, you can run them as many times you want, you just have to follow the good execution order described below. If a step fails, just retry the previous one on so on until it succeed :p

#### 1. Tests changes

Write and modify paasify code. Once you feel ready, you can start with this process.

First start to run the test suite:
```
task run_tests
```

If tests os OK, stage your changes into git. Don't try to commit yet, because `pre-commit` will prevent you to do so. You can still try tho ;-)
```
git status -sb
git diff
git add file1 file2 ...
```

Check you have no unstaged files left, because some later steps will refuse to run if you have unstaged files (like the `fix_qa` command).

#### 2. Quality verifications

Let's run automatic code linting:
```
task fix_qa

# Then review changes and add them to staging again
git diff
git add -u
```
This task will reformat your code with black, but black will refuse to run if files are not staged.


Your code is now properly formatted, we will now check basic code quality:

```
task run_qa
```

Output may be pretty verbose, you just have to focus on fixing Errors and above. Other levels should ideally be fixed as well. You may at this time rewrite small portions of your code to be able to pass this tests.

If everything is fine, stage again your modified files into git. And now, you can restart the whole thing from the beginning. If you didn't have to stage new changes, and only then, you can continue to the following step.


#### 3. Commit message standards

Your staged files are ready to be commited. If you have a small commit:
```
git commit -m "feat: add this feature to this thing" .
```

For bigger commit, please follow the keepachangelog format, otherwise you will hit this wall:

```
commit validation: failed!
please enter a commit message in the commitizen format.
commit "": "this is my change, but not a valid commit"
pattern: (?s)(build|ci|docs|feat|fix|perf|refactor|style|test|chore|revert|bump)(\(\S+\))?!?:( [^\n\r]+)((\n\n.*)|(\s*))?$
```



## Hacking docker image

Build docker image:
```
task docker_build_image
```

Then you can run your current paasify in docker:
```
task docker_run -- --version
```

### Tips

Test dockerized paasify with your project:
```
alias paasify-docker='docker run -ti --rm -v $(dirname $PWD):/work -w /work/$(basename $PWD) paasify:latest paasify'

# Run command from outside
paasify-docker info

# To get into your project
docker run -ti --rm -v $(dirname $PWD):/work -w /work/$(basename $PWD) bash
```

## Push upstream


From there, open a pull request on github to have your changes incorporated 
into the project. And thanks to you for your contribution <3

