#!/usr/bin/env sh

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

. scripts/common.sh

SOURCE_ROOT=$(pwd)

section_open "Check if the necessary dependencies are available: gcloud, terraform"
    check_exec_dependency "gcloud"
    check_exec_version "gcloud"
    check_exec_dependency "terraform"
    check_exec_version "terraform"
section_close

section_open "Check if the necessary variables are set: PROJECT_ID"
    check_environment_variable "PROJECT_ID" "the Google Cloud project that Terraform will provision the resources in"
section_close

section_open  "Setting the Google Cloud project to: ${PROJECT_ID}"
    gcloud config set project "${PROJECT_ID}"
section_close

section_open  "SDK login"
    gcloud auth login --update-adc
section_close

# section_open "Setting Google Application Default Credentials"
#     set_application_default_credentials "${SOURCE_ROOT}"
# section_close

section_open "Enable all the required APIs"
    enable_all_apis
section_close

section_open "Check and try to set required org-policies on project: ${PROJECT_ID}"
    check_and_set_policy_rule "compute.vmExternalIpAccess" "allowAll: true" '"allowAll": true'  "${PROJECT_ID}"
    check_and_set_policy_rule "compute.requireShieldedVm" "enforce: false" '"enforce": false' "${PROJECT_ID}"
    check_and_set_policy_rule "iam.allowedPolicyMemberDomains" "allowAll: true" '"allowAll": true' "${PROJECT_ID}"
section_close

