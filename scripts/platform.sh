#!/bin/bash

# Little script helper to detect current platform


set -eu

# Environment vars
# =================
TOOL_POETRY_VERSION='1.3.2'
TOOL_DIRENV_VERSION='2.31.0'
# See: https://github.com/go-task/task/releases
TOOL_TASK_VERSION='3.18.0'
TOOL_GH_VERSION='2.23.0'

# Usage
# =================
usage ()
{
  cat <<EOF
  Helps to retrieve current platform information

  Usage: ${0} [OPTIONS,...]

  OPTIONS:
    env                   Show environment vars
    os                    Show platform OS
    platform              Show platform architecture
    tool                  Show all tools versions
    tool NAME             Show tool versions

  EXAMPLES:
    ${0} env
    ${0} os
    ${0} platform
    . \$(${0} env)

EOF

}


# Show environment context
# =================
guess_plat ()
{
  local result=

  result=$(uname --machine)
  case "$result" in
    x86_64)
      echo "amd64"
      ;;
    *)
      >&2 echo "ERROR: Unsupported platform: $result"
  esac
}

guess_os ()
{
  local result=

  result=$(uname --operating-system)
  case "$result" in
    GNU/Linux)
      echo "linux"
      ;;
    *)
      >&2 echo "ERROR: Unsupported OS: $result"
  esac
}

guess_venv ()
{
  if command -v virtualenv >/dev/null; then
    echo "virtualenv"
  else
    echo "python -m venv"
  fi
}

# Show utils versions
# =================
show_version ()
{
  local name=$1
  local var=$2

  set +eu
  if [[ -n "${!var}" ]] ; then
    >&2 echo "INFO: Version for $name: ${!var}"
    echo "${!var}"
  else
    >&2 echo "ERROR: Unsupported tool: ${name}"
  fi
  set +eu
}

show_versions ()
{
  local tools=${1:-}
  local var_names=

  # Detect tools
  if [[ -z "$tools" ]]; then
    var_names=${!TOOL_*}
  else
    for tool in $tools; do
      var_names="$var_names TOOL_${tool^^}_VERSION"
    done
  fi

  # Show each tools
  local name=
  for var in $var_names; do
    name=$( echo "$var" | sed 's/TOOL_//;s/_VERSION//')
    name=${name,,}
    show_version $name $var
  done

}

# Environment
# =================
show_env ()
{
  cat 2>/dev/null <<EOF
export PROJECT_REPO=${PROJECT_REPO:-barbu-it/paasify}
export PROJECT_REMOTE_NAME=${PROJECT_REMOTE_NAME:-origin}
export PROJECT_OS=${PROJECT_OS:-$(guess_os)}
export PROJECT_ARCH=${PROJECT_ARCH:-$(guess_plat)}

export PROJECT_POETRY_VERSION=${PROJECT_POETRY_VERSION:-$(show_versions poetry)}
export PROJECT_GH_VERSION=${PROJECT_GH_VERSION:-$(show_versions gh)}
export PROJECT_TASK_VERSION=${PROJECT_TASK_VERSION:-$(show_versions task)}

export PROJECT_VENV_CMD=${PROJECT_VENV_CMD:-$(guess_venv)}
EOF
}


# Main
# =================
main ()
{
  local action=${1:-help}
  shift 1 || true

  case "$action" in
    help|--help|-h)
      usage
      ;;
    os)
      guess_os
      ;;
    venv)
      guess_venv
      ;;
    plat|platform)
      guess_plat
      ;;
    tool|version)
      show_versions ${1-}
      ;;
    env|environ*)
      show_env
      ;;
    *)
      >&2 echo "ERROR: Unknown command: $action"
      usage
      exit 1
      ;;
  esac

}

main ${@-}
