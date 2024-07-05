#!/bin/bash
#
# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

CLOUD_FUNC_DIR=$(realpath $(dirname $0))

# Validate arguments
if [ $# -ne 1 ]; then
  echo "Please run $0 <package-dir>"
  exit 1
fi
if [ \! -d "$1" ]; then
  echo "$1 is not a directory"
fi
PACKAGE_DIR=$(realpath $1)

# Clear out old package
rm -r "${PACKAGE_DIR}"/*

# Copy in files fresh
(
  cd "${CLOUD_FUNC_DIR}"
  cp \
    README.md \
    deploy.sh \
    main.py \
    requirements.txt \
    "${PACKAGE_DIR}"
  mkdir -p "${PACKAGE_DIR}/libs"
  cp -r ../../libs/* "${PACKAGE_DIR}/libs"
)
