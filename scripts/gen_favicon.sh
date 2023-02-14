#!/bin/bash

# Usage example:
# gen_favicon.sh SVG_FILE.svg OUT_FILE.ico

set -eu

# Generate favicon from official logo
convert -density 300 -define icon:auto-resize=256,128,96,64,48,32,16 -background none $1 $2

