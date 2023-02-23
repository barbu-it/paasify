#!/bin/bash
#
# Install project development utils
# Only install non-python dependencies, binaries must
# be installed in $VIRTUAL_ENV/bin path


set -eu

_VENV=${VIRTUAL_ENV:-.venv}
PLAT=${PROJECT_OS:-linux}
ARCH=${PROJECT_ARCH:-amd64}

GH_VERSION=${PROJECT_GH_VERSION:-latest}
TASK_VERSION=${PROJECT_TASK_VERSION:-latest}
POETRY_VERSION=${PROJECT_POETRY_VERSION:-latest}

usage ()
{
  cat <<EOF
  Install project development utils in local venv

  Usage: ${0}

EOF
}


download_github_release() {
  local version=$1
  local repository=$2
  local file=$3
  local bin_dir=$4

  local select=
  if [[ -n "${5}" ]]; then
    select="$5"
      shift 1
  fi

  local dirs_=$(grep -o '/' <<< "$select")
  dirs_=$(( ${#dirs_} - 1 ))

  # Tofix: strip components should be calculated from the number of // in file

  # Télécharge la release avec la version spécifiée
    # https://github.com/cli/cli/releases/download/v2.23.0/gh_2.23.0_linux_amd64.tar.gz
  curl -s -L -o - "https://github.com/$repository/releases/download/$version/$file" | tar -xz --strip-components ${dirs_}  -C "$bin_dir" $select

}




install_venv ()
{
  if [[ -d "${_VENV}/bin" ]] ; then
    echo "INFO: Python VirtualEnv already installed in: ${_VENV}"
  else
    echo "INFO: Installing Python Virtualenv: ${_VENV}"
    virtualenv ${_VENV}
  fi
}

enable_venv ()
{
    echo "INFO: Enabling venv: ${_VENV}"
  . ${_VENV}/bin/activate
}


install_poetry ()
{
  if ! is_present poetry $POETRY_VERSION --version; then
    echo "INFO: Installing Poetry"
    pip install poetry==$POETRY_VERSION
  fi
}

install_task ()
{
  if ! is_present task $TASK_VERSION --version; then
    echo "INFO: Installing Task"
    sh -c "$(curl -s --location https://taskfile.dev/install.sh)" -- -d -b ${VIRTUAL_ENV}/bin v$TASK_VERSION
  fi
}

install_gh ()
{
  if ! is_present gh $GH_VERSION --version; then
    echo "INFO: Installing gh"
    # https://github.com/cli/cli/releases/download/v2.23.0/gh_2.23.0_linux_amd64.tar.gz
    download_github_release "v${GH_VERSION}" cli/cli gh_${GH_VERSION}_${PLAT}_${ARCH}.tar.gz $_VENV/bin gh_${GH_VERSION}_${PLAT}_${ARCH}/bin/gh
  fi
}

install_python_deps ()
{
  poetry install -vv --no-interaction --no-root
}


install_pre_commit ()
{
  if is_present pre-commit; then
    echo "INFO: Installing pre-commit hooks into git"
    poetry run pre-commit install --install-hooks
  fi
}


is_present ()
{
  local app=$1
  local version=${2-}
  shift 2 || true

  if command $app >&/dev/null; then

    if [[ -z "$version" ]]; then
      echo "INFO: $app is already present"
      return 0
    else

      if grep -q "$version" <<< "$($app $@)"; then
      echo "INFO: $app is already present in version $version"
        return 0
      else
        return 1
      fi

    fi

  else
    return 1
    # https://github.com/cli/cli/releases/download/v2.23.0/gh_2.23.0_linux_amd64.tar.gz
    download_github_release "v${GH_VERSION}" cli/cli gh_${GH_VERSION}_${PLAT}_${ARCH}.tar.gz $_VENV/bin gh_${GH_VERSION}_${PLAT}_${ARCH}/bin/gh
  fi
}

main ()
{

  # Base
  install_venv
  enable_venv
  install_poetry
  install_task

  # Python
  install_python_deps
  install_pre_commit

  # Extras
  install_gh

}


main ${@}
