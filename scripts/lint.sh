#!/usr/bin/env bash

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

set -o errexit
set -o nounset
set -o pipefail

echo "Running lint checks"

LINT_CI_JOB_PATH=".github/workflows/lint.yaml"
DEFAULT_LINTER_CONTAINER_IMAGE_VERSION="$(grep <"${LINT_CI_JOB_PATH}" "super-linter/super-linter" | awk -F '@' '{print $2}' | head --lines=1)"

LINTER_CONTAINER_IMAGE="ghcr.io/super-linter/super-linter:${LINTER_CONTAINER_IMAGE_VERSION:-${DEFAULT_LINTER_CONTAINER_IMAGE_VERSION}}"

echo "Running linter container image: ${LINTER_CONTAINER_IMAGE}"

SUPER_LINTER_COMMAND=(
  docker run
)

if [ -t 0 ]; then
  SUPER_LINTER_COMMAND+=(
    --interactive
    --tty
  )
fi

if [ "${LINTER_CONTAINER_OPEN_SHELL:-}" == "true" ]; then
  SUPER_LINTER_COMMAND+=(
    --entrypoint "/bin/bash"
  )
fi

if [ "${LINTER_CONTAINER_FIX_MODE:-}" == "true" ]; then
  SUPER_LINTER_COMMAND+=(
    --env-file ".github/linters/super-linter-fix-mode.env"
  )
fi

SUPER_LINTER_COMMAND+=(
  --env RUN_LOCAL="true"
  --env-file ".github/linters/super-linter.env"
  --name "super-linter"
  --rm
  --volume "$(pwd)":/tmp/lint
  --volume /etc/localtime:/etc/localtime:ro
  --workdir /tmp/lint
  "${LINTER_CONTAINER_IMAGE}"
  "$@"
)

echo "Super-linter command: ${SUPER_LINTER_COMMAND[*]}"
"${SUPER_LINTER_COMMAND[@]}"
