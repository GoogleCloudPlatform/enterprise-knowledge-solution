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

section_open "Check if the necessary dependencies are available: gcloud, terraform"
check_exec_dependency "gcloud"
check_exec_version "gcloud"
check_exec_dependency "terraform"
check_exec_version "terraform"
section_close

section_open "Check and set mandatory environment variables"
check_environment_variable "PROJECT_ID" "the Google Cloud project where resources are created"
check_environment_variable "REGION" "the Google Cloud region where resources are created"
check_environment_variable "IAP_ADMIN_ACCOUNT" "the user or group configured as the contact for IAP consent screen"
set_active_principal
gcloud config unset billing/quota_project
gcloud config set project "${PROJECT_ID}"
section_close

section_open "Enable the required APIs for bootstrap scripts"
enable_bootstrap_apis
section_close

section_open "Setup OAuth consent screen (brand) required for IAP"
create_oauth_consent_config
section_close

section_open "Create deployer service account and enable $ACTIVE_PRINCIPAL to use service account impersonation "
create_service_account_and_enable_impersonation
section_close

section_open "Enable all the required IAM roles for deployer service account, serviceAccount:""${SERVICE_ACCOUNT_ID}"""
enable_deployer_roles "${SERVICE_ACCOUNT_ID}"
section_close

section_open "Explicitly declare underlying permissions for Cloud Build processes"
enable_builder_roles
section_close

section_open "Build and push container image to Artifact Registry for Form Processor"
../../components/processing/form_parser/build/build_container_image.sh
section_close

section_open "Set Application Default Credentials to be used by Terraform"
set_adc
section_close
