#!/bin/bash

set -eu -o pipefail

main () {

  if pytest  test_store_base.py  test_store_template.py; then
    echo "OK"
  else
    echo "FAILED"
    return 2
  fi
}

main
