#!/usr/bin/env bash

# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -o errexit
set -o nounset

# shellcheck source=/dev/null
. scripts/common.sh

section_open "Check that necessary environment variables are set"
check_mandatory_variable "PROJECT_ID" "set the PROJECT_ID where IAM roles will be applied"
section_close

section_open "Enable required IAM roles for the UPLOADER persona"
check_and_set_persona "UPLOADER"
section_close

section_open "Enable required IAM roles for the DEPLOYER persona"
check_and_set_persona "DEPLOYER"
section_close

section_open "Enable required IAM roles for the OPERATOR (read-only) persona"
check_and_set_persona "OPERATOR_READONLY"
section_close

section_open "Enable required IAM roles for the OPERATOR (read & write) persona"
check_and_set_persona "OPERATOR_READWRITE"
section_close

section_open "Enable required IAM roles for the READER persona"
check_and_set_persona "READER"
section_close