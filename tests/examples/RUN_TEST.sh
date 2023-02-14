#!/bin/bash


set -eu

check_project ()
{
  git st .
  paasify build
  git -P st .
  git -P diff --ignore-matching-lines=$PWD .
}


main ()
{
  # TODO: unit_stacks_src
  #local tests="minimal unit_stacks_idents_dup_fail var_merge minimal"
  local tests="var_merge real_tests"
  for i in $tests; do
    echo "==========  Testing dir: $i"
    (
      cd $i
      check_project
    )

  done

  return
  paasify build  && git diff --no-prefix

  echo "It must not have changed, otherwise API has been broken"
}


main $@
