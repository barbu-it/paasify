#!/bin/bash


DRY_MODE=true
CMD_OPTS=

set -eu

usage ()
{
  cat <<EOF
  Helps to bump project version according to git status

  Usage: ${0} [OPTIONS,...]

  OPTIONS:
    alpha,beta,rc         Force version type
    major,minor,patch     Force version type
    INTEGER               Positive number for dev releases

  EXAMPLES:
    ${0} beta
    ${0} beta 2
    ${0} minor alpha 3

EOF
}

parse_args ()
{
  local branch=$1 pre_opts= bump_opts= dev_opts= dry_opts= other=
  shift 1

  case "$branch" in
    main)
      >&2 echo "INFO: Detecting main branch"
      ;;
    devel*)
      >&2 echo "INFO: Detecting devel branch"
      #pre_opts="--prerelease rc"
      pre_opts="--prerelease alpha"
      ;;
    *)
      dev_opts="--local-version"
      ;;
  esac

  while [[ -n "${1-}" ]]; do
    case $1 in
      dry|-n|--dry)
        >&2 echo "INFO: Dry mode enabled"
        DRY_MODE=true
        ;;
      exec|-x|--exec)
        >&2 echo "INFO: Dry mode disabled"
        DRY_MODE=false
        ;;
      help|-h|--help)
        >&2 usage
        exit 1
        ;;

      alpha|beta|rc)
        pre_opts="--prerelease $1"
        ;;
      major|minor|patch)
        bump_opts="--increment $1"
        ;;
      [0-9]*)
        dev_opts="--devrelease $1"
        ;;
      *)
        >&2 echo "WARN: Forcing manual version: $1"
        other="$other $1"
        ;;
    esac
    shift
  done

  dry_opts=''
  if $DRY_MODE; then
    dry_opts="--dry-run"
    >&2 echo "INFO: Dry mode enabled, use with --exec to run changes"
  fi

  CMD_OPTS="$dry_opts $pre_opts $dev_opts $bump_opts $other"

}

check_git_files ()
{
  local files='pyproject.toml paasify/version.py VERSION_NOTES.md'
  local st=
  st=$(git status --porcelain $files)

  if grep -q '^.M ' <<< "$st"; then
    >&2 echo "ERROR: Uncomitted version files !"
    exit 1
  fi
}

validate_version ()
{
  local version= out=
  out=$(paasify --version)
  version=${1:-$out}

  if ! grep -q "$version" <<< "$out"; then
    >&2 echo "ERROR: Expected version '$version', 'paasify --version' returned: $out"
    exit 1
  fi

  out=$(cz version --project)
  if ! grep -q "$version" <<< "$out)"; then
    >&2 echo "ERROR: Expected version '$version', 'cz version --project' returned: $out"
    exit 1
  fi

  out=$(poetry version)
  if ! grep -q "$version" <<< "$out)"; then
    >&2 echo "ERROR: Expected version '$version', 'poetry version' returned: $out"
    exit 1
  fi

  out=$(git tag --list)
  if ! grep -q "$version" <<< "$out)"; then
    >&2 echo "ERROR: Expected version '$version' in 'git tag'"
    exit 1
  fi

}

generate_partial_changelog ()
{
  local dest=$1
  >&2 echo "INFO: Generate partial changelog in $dest"
  cz changelog --dry-run --incremental --unreleased-version 'Last changes' > "$dest"

}

main ()
{
  #set -x
  local branch=
  branch=$( git rev-parse --abbrev-ref HEAD )
  parse_args "$branch" ${@-}


  # Sanity checks
  validate_version
  if ! $DRY_MODE ; then
    case "$branch" in
      main|develop) :;;
      *)
        >&2 echo "ERROR: Tags are not allowed on $branch"
        exit 1
        ;;
    esac
    check_git_files
    generate_partial_changelog VERSION_NOTES.md
  fi

  # Show output
  >&2 echo "INFO: Changelog to be generated:"
  >&2 echo "DEBUG: command: cz bump --changelog $CMD_OPTS"
  cz bump --changelog $CMD_OPTS

}


main ${@}
