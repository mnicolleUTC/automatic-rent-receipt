#!/bin/bash

# Copy either authentic folder content or example folder content based on 
# the existence of one folder

mkdir used_files

if [ -d authentic_files ]; then \
    cp -rf authentic_files/* used_files
else \
    cp -rf example_files/* used_files
fi