#!/bin/bash

set -eu

DEBUG=${DEBUG:-false}

show_mode ()
{
  local mode=$1

  if [[ "$mode" == "pkg" ]]; then
    echo "$2"
  elif [[ "$mode" == "git" ]]; then
    echo "$3"
  elif [[ "$mode" == "docker" ]]; then
    echo "$4"
  elif [[ "$mode" == "release" ]]; then
    echo "$5"
  else
    echo "Not implemented: ${mode}, please choose between: pkg, docker, git, release"
    return 1
  fi
}

main ()
{
  local mode=$1
  local git_tag=$(git describe --tags 2>/dev/null)
  local git_branch=$(git rev-parse --abbrev-ref HEAD)

  #local pkg_version=$(poetry version -s)
  local pkg_version=$(python -m paasify.version 2>/dev/null)

  if [[ -n "$git_tag" ]]; then
    $DEBUG && >&2 echo "Mode: Release Tag"
    show_mode $mode "$pkg_version" "$git_tag" "$pkg_version" true
  else
    local git_branch=$(git rev-parse --abbrev-ref HEAD)
    if [[ "$git_branch" =~ ^v.* ]]; then
      $DEBUG && >&2 echo "Mode: Release Branch"
      show_mode $mode  "$pkg_version" "$git_tag" "$pkg_version" true
    else
      $DEBUG && >&2 echo "Mode: Release Latest"
      show_mode $mode "$pkg_version" "$git_tag" "latest" false
    fi
  fi
}

main $@


