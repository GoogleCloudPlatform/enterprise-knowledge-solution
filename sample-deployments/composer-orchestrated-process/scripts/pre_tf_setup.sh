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

. scripts/common.sh

SOURCE_ROOT=$(pwd)

section_open "Check if the necessary dependencies are available: gcloud, terraform"
    check_exec_dependency "gcloud"
    check_exec_version "gcloud"
    check_exec_dependency "terraform"
    check_exec_version "terraform"
section_close

section_open "Check and set PROJECT_ID"
    check_environment_variable "PROJECT_ID" "the Google Cloud project that Terraform will provision the resources in"
    gcloud config set project "${PROJECT_ID}"
section_close

<<<<<<< HEAD
<<<<<<< HEAD
=======
#section_open  "SDK login for the user "
#    gcloud auth login
#    gcloud auth application-default login --impersonate-service-account=${SERVICE_ACCOUNT_ID}
#section_close

>>>>>>> 7773aba (initial commit. Add minimum set of IAM roles to the setup script. Further testing required to simplify friciton of bootstrapping the SA, dealing with org policies. and behavior where AR is still trying to use the default compute sa)
=======
>>>>>>> ee09c45 (Improve setup script to to check for effective org policies inherited to this project, not just the setting of an org policy directly at this project)
section_open "Enable the required APIs "
    enable_all_apis
section_close

section_open "Enable all the required IAM roles for deployer service account, serviceAccount:"${SERVICE_ACCOUNT_ID}""
<<<<<<< HEAD
<<<<<<< HEAD
    enable_deployer_roles  "${SERVICE_ACCOUNT_ID}"
section_close

section_open "Explicitly declare underlying permissions for Cloud Build processes"
    enable_builder_roles
section_close


section_open "Check and try to set required org-policies on project: ${PROJECT_ID}"
<<<<<<< HEAD
    check_and_set_policy_rule "compute.vmExternalIpAccess" "allowAll: true" '"allowAll": true'  "${PROJECT_ID}"
    check_and_set_policy_rule "compute.requireShieldedVm" "enforce: false" '"enforce": false' "${PROJECT_ID}"
    check_and_set_policy_rule "iam.allowedPolicyMemberDomains" "allowAll: true" '"allowAll": true' "${PROJECT_ID}"
=======
    enable_all_roles  "${SERVICE_ACCOUNT_ID}"
=======
    enable_deployer_roles  "${SERVICE_ACCOUNT_ID}"
>>>>>>> db5b804 (Fixed permission issues to create Images in AR that relied on legacy (deprecated) Cloud Build SA)
section_close

section_open "Explicitly declare underlying permissions for Cloud Build processes"
    enable_builder_roles
section_close

##TODO:need to use policy analyzer to check effective policy. Can't assume the user always wants to remove the constraint.
#section_open "Check and try to set required org-policies on project: ${PROJECT_ID}"
=======
>>>>>>> ee09c45 (Improve setup script to to check for effective org policies inherited to this project, not just the setting of an org policy directly at this project)
    check_and_set_policy_rule "compute.vmExternalIpAccess" "allowAll: true" '"allowAll": true'  "${PROJECT_ID}"
    check_and_set_policy_rule "compute.requireShieldedVm" "enforce: false" '"enforce": false' "${PROJECT_ID}"
    check_and_set_policy_rule "iam.allowedPolicyMemberDomains" "allowAll: true" '"allowAll": true' "${PROJECT_ID}"
section_close

section_open  "Set Application Default Credentials to be used by Terraform"
    gcloud auth application-default login --impersonate-service-account=${SERVICE_ACCOUNT_ID}
>>>>>>> 7773aba (initial commit. Add minimum set of IAM roles to the setup script. Further testing required to simplify friciton of bootstrapping the SA, dealing with org policies. and behavior where AR is still trying to use the default compute sa)
section_close

section_open  "Set Application Default Credentials to be used by Terraform"
    gcloud auth application-default login --impersonate-service-account=${SERVICE_ACCOUNT_ID}
section_close

section_open "Build and push container image to Artifact Registry for Form Processor"
    ../../components/processing/form_parser/build/build_container_image.sh
section_close
<<<<<<< HEAD
=======
<<<<<<< HEAD

=======
>>>>>>> 5cb91ac (Improve the "deploying the sample" guidance under README)
>>>>>>> 5e6b8ab (Improve the "deploying the sample" guidance under README)
