## Last changes (2023-02-22)

### feat

- provides internal stack variables to users
- rework ls explain output for easier comprehension
- improve error message on variables failures
- add support for PAASIFY_ENV_COLLECTION_DIR

### fix

- too verbose environment var usage notice
- default collection README typos and requirements.txt
- outdated default project settings
- variable parser internal behavior
- weird docker bug handling weirdly symlinks
- case when short variables are concat with other value
- variables dependency resolution order
- parser was not parsing vars in correct order
- developper deployment scripts

### docs

- fix typo in toc

### chore

- linting
- refactor default collection path guessing

### ci

- move tests function in a common lib
- fix debian support for virtualenv

### test

- Update minor changes in tests
- update cli tests with regression data

