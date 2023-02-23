#!/bin/bash

_VENV=${VIRTUAL_ENV:-.venv}
COMP_DIR=${_VENV}/comp/

>&2 echo "INFO: Load environment vars"
eval "$(./scripts/platform.sh env)"

if [[ ! -f "$_VENV/bin/poetry" ]]; then
  >&2 echo "INFO: Install project dependencies"
  ./scripts/bootstrap_deps.sh
  . $_VENV/bin/activate
  task completion
else
  >&2 echo "INFO: Load virtualenv"
  . $_VENV/bin/activate
fi


if [[ ! -f "$_VENV/bin/paasify" ]]; then
  >&2 echo "INFO: Install paasify"
  task setup
fi

>&2 echo "INFO: Load completions directory: ${COMP_DIR}"
for i in "$COMP_DIR"*.sh; do
  comp=${i##*/}
  if [[ ! -f "$i" ]]; then
    >&2 echo "INFO: No completion found, please run: task completion"
    continue
  fi
  >&2 echo "INFO: Loading completion: ${comp}"
  source "$i"
done

