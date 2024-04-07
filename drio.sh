#!/usr/bin/env bash
# Create a new drawio file from a template and open it


set -eu

file_name="$1"

# Name of drawio template file
# TEMPLATE_FILE=
# TARGET_FOLDER=

# Check if template file exists
if ! [[ -f $TEMPLATE_FILE ]]; then
  echo "Template file at ${TEMPLATE_FILE} does not exist, exiting.."
  exit 1
fi

# Check if the input contains characters that are not allowed in a filename
if [[ "${file_name}" =~ [^a-zA-Z0-9_\.-] ]]; then
  echo "Invalid characters found in the file name."
  exit 1
fi

# Check if the input is a valid file name
if [ -e "${TARGET_FOLDER}/${file_name}" ]; then
  echo "File already exists."
  exit 1
fi

if [[ "${file_name}" =~ ^(.+)"."drawio$ ]]; then
  echo "File name already ends with drawio"
else
  file_name="${file_name}.drawio"
fi

target_file="${TARGET_FOLDER}/${file_name}"
cp -n "$TEMPLATE_FILE" "$target_file"

open $target_file
