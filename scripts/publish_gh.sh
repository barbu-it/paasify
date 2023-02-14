#!/bin/bash
#
# Publish release on github


set -eu

LATEST=false
DRAFT=false
PRERELEASE=false
SKIP_EXISTING=true
CMD_OPTS=

usage ()
{
  cat <<EOF
  Publish on github releases

  Usage: ${0}

EOF
}

parse_args ()
{
  local branch=$1
  shift 1

  case "$branch" in
    main)
      >&2 echo "INFO: Detecting main branch"
      LATEST=true
      ;;
    *)
      >&2 echo "INFO: Detecting devel branch, making a prerelease draft"
      DRAFT=true
      PRERELEASE=true
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

      latest)
        LATEST=true
        ;;
      no-latest)
        LATEST=false
        ;;

      draft)
        DRAFT=true
        ;;
      no-draft)
        DRAFT=false
        ;;

      prerelease)
        PRERELEASE=true
        ;;
      no-prerelease)
        PRERELEASE=false
        ;;


      *)
        >&2 echo "WARN: Forcing manual version: $1"
        other="$other $1"
        ;;
    esac
    shift
  done

  local out=

  $LATEST && out="$out --latest"
  $DRAFT && out="$out --draft"
  $PRERELEASE && out="$out --prerelease"

  CMD_OPTS="$out"
}




publish_gh ()
{
  local repo=$1
  local version=$2
  local note_file=${3-}
  local title=${4:-Release $version}

  if [[ -n "$note_file" ]]; then
    note_file="--notes-file $note_file"
  else
    note_file="--generate-notes"
  fi

  # Check if a realease already exists:
  if gh --repo "$repo" release view "$version" 2>&1 | grep -q 'release not found'; then
    :
  else
    if $SKIP_EXISTING; then
      >&2 echo "WARN: A '$version' release already exists, skip Github upload"
      return 0
    else
      >&2 echo "INFO: Replace existing Github release '$version'"
      gh --repo "$repo" release delete "$version" --yes
    fi
  fi

  # Push release
  set -x
  gh --repo "$repo" release create "$version" --title "$title" $note_file $CMD_OPTS dist/*
  >&2 echo "INFO: Published on Github !"
}

gen_release_msg ()
{
  cat <<EOF
Release $VERSION, published date: $(date)

List of changes:

EOF
  tail -n +2 VERSION_NOTES.md
}

main ()
{
  local VERSION=$(paasify --version)
  branch=$( git rev-parse --abbrev-ref HEAD )
  parse_args $branch ${@}

  if [[ -f "VERSION_NOTES.md" ]] ; then
    gen_release_msg > dist/RELEASE.md
    publish_gh barbu-it/paasify v$VERSION dist/RELEASE.md
  else
    publish_gh barbu-it/paasify v$VERSION
  fi

  #publish_gh barbu-it/paasify v$VERSION dist/RELEASE.md

}


main ${@}

