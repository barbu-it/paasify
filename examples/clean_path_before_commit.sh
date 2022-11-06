#!/bin/bash

# Note, actually, we should replace all ABS path from the project root
# not from home ...

grep -rl $HOME . | xargs sed -i "s#$HOME#\$HOME#g"

echo "All \$HOME occurences has been replaced"

