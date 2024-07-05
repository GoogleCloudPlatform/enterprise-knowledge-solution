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

ROOT="$(realpath $(dirname $0))"
VENV="${ROOT}/.venv"
[ -d "${VENV}" ] || (
  cd "${ROOT}"

  # Create and bootstrap the virtual environment
  python3 -m venv "${VENV}"
  "${VENV}/bin/python3" -m pip install -q --require-hashes -r "${ROOT}/reqs/requirements_bootstrap.txt"

  # Synchronize the environment
  "${VENV}/bin/python3" -m invoke sync
)

DOTENV="${ROOT}/.env"
if [ -f "${DOTENV}" ]; then
  set -o allexport
  source "${DOTENV}"
  set +o allexport
fi

CMD="$1"
shift

if [ ! -f "${VENV}/bin/${CMD}" ]; then
  echo "Usage: $(basename $0) command [... command args]"
  echo ""
  echo "Command is a bin available in the virtual environment,"
  echo "including python3 interpreter itself."
  exit 1
fi

exec "${VENV}/bin/${CMD}" "$@"
