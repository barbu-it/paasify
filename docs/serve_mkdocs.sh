#!/bin/bash

# Generate API doc
./gen_apidoc.sh

# Run server
mkdocs serve
