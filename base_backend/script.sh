#!/bin/bash

# Define the two directories
DIR1="tests/collaboration"
DIR2="temp/tests/collaboration"

# Compare directories recursively and filter for files that differ
echo "Files with differences:"
echo "====================="

diff -qr "$DIR1" "$DIR2" | grep "^Files" | while read -r line; do
    # Extract just the filename from the diff output
    # The format is: "Files src/path/file.py and temp/src/path/file.py differ"
    file=$(echo "$line" | awk '{print $2}' | sed "s|$DIR1/||")
    echo "$file"
done

