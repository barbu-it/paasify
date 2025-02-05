#!/bin/bash

set -eu -o pipefail

main_examples () {
  names="poc2.py poc3.py"

  for name in $names; do
    if python "$name" ; then
      echo "OK"
    else
      echo "FAILED: $name"
      return 2
    fi
  done

}

main_tests () {

  if pytest  test_store_base.py  test_store_template.py $@ ; then
    echo "OK"
  else
    echo "FAILED"
    return 2
  fi
}

main_examples
main_tests
