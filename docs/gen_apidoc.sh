#!/bin/bash

set -eu


BUILD_DIR_SCHEMA=./src/jsonschemas
BUILD_DIR_DOC=./src/refs/config
BUILD_DIR_RAW=./src/refs/raw
BUILD_DIR_SCHEMA=$BUILD_DIR_RAW
SCHEMA_TARGETS="app prj prj_config prj_stacks prj_sources"

gen_jupiter_doc()
{
  python -m bash_kernel.install

}

gen_schema()
{
  for target in $SCHEMA_TARGETS ; do
    echo "Generate $target schema"
    paasify schema --format=json $target > $BUILD_DIR_SCHEMA/paasify_${target}_schema.json
    paasify schema --format=yaml $target > $BUILD_DIR_SCHEMA/paasify_${target}_schema.yml
  done
}

gen_doc()
{
  for target in $SCHEMA_TARGETS ; do
    for out in "md" "html" ; do
      echo "Generate $target documentation ($out)"
      generate-schema-doc --config-file doc_schema_${out}.yml $BUILD_DIR_SCHEMA/paasify_${target}_schema.json $BUILD_DIR_DOC
    done
  done
}

gen_cli_usage()
{
  COLUMNS=82 paasify --help > $BUILD_DIR_RAW/cli_usage.txt
}

main ()
{
  echo "Documentation build script"

  mkdir -p $BUILD_DIR_SCHEMA $BUILD_DIR_RAW $BUILD_DIR_DOC

  gen_cli_usage
  gen_schema
  gen_doc

  echo "Documentation succesfully genereated !"
}

#mkdir -p $BUILD_DIR/html $BUILD_DIR/md
#generate-schema-doc --config-file doc_schema_html.yml $BUILD_DIR/paasify_yml_schema.json $BUILD_DIR/html
#generate-schema-doc --config-file doc_schema_md.yml $BUILD_DIR/paasify_yml_schema.json $BUILD_DIR/md


# Temporary project example !

# Generate plugin documentation
# paasify --config ../examples/ex3/devbox_core/paasify.yml  explain --mode src/plugins_apidoc


main $0

