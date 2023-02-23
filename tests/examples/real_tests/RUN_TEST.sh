#!/bin/bash


paasify build  && git diff --no-prefix .


echo "It must not have changed, otherwise API has been broken"
