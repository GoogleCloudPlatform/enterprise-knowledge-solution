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

ERR_VARIABLE_NOT_DEFINED=2
ERR_MISSING_DEPENDENCY=3

CYAN='\033[0;36m'
BCYAN='\033[1;36m'
NC='\033[0m' # No Color
DIVIDER=$(printf %"$(tput cols)"s | tr " " "*")

# DISPLAY HELPERS

section_open() {
  section_description=$1
  printf '%s' "$DIVIDER"
  printf "${CYAN} %s ${NC} \n" "$section_description"
  printf '%s' "$DIVIDER"
}

section_close() {
  printf '%s' "$DIVIDER"
  printf "${CYAN} %s ${BCYAN}- done${NC} \n" "$section_description"
  printf "\n\n"
}

check_exec_dependency() {
  EXECUTABLE_NAME="${1}"

  if ! command -v "${EXECUTABLE_NAME}" >/dev/null 2>&1; then
    echo "[ERROR]: ${EXECUTABLE_NAME} command is not available, but it's needed. Make it available in PATH and try again. Terminating..."
    exit ${ERR_MISSING_DEPENDENCY}
  fi

  unset EXECUTABLE_NAME
}

set_active_principal() {
  local __active_principal
  __active_principal=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
  if echo "$__active_principal" | grep "iam.gserviceaccount.com"; then
    ACTIVE_PRINCIPAL="serviceAccount:${__active_principal}"
  else
    ACTIVE_PRINCIPAL="user:${__active_principal}"
  fi
  unset __active_principal
}

create_oauth_consent_config() {
  create_custom_role_iap
  enable_role "projects/$PROJECT_ID/roles/customIAPAdmin" "$ACTIVE_PRINCIPAL" "projects/$PROJECT_ID"
  echo "Check if OAuth Consent Screen (brand) already exists"
  set +e # Disable errexit
  __iap_brand="$(gcloud iap oauth-brands list --format='get(name)')"
  set -e # Re-enable errexit
  if [[ $__iap_brand ]]; then
    echo "OAuth Consent Screen (brand) $__iap_brand has already been created"
  else
    gcloud iap oauth-brands create --application_title="Enterprise Knowledge Search Web-UI" \
      --support_email="$IAP_ADMIN_ACCOUNT"
  fi
  unset __iap_brand
}

create_custom_role_iap() {
  set +e # disenable errexit
  __customIapAdmin=$(gcloud iam roles list --project="$PROJECT_ID" | grep customIAPAdmin)
  set -e # Re-enable errexit
  if [[ $__customIapAdmin ]]; then
    echo "Custom role projects/$PROJECT_ID/roles/customIAPAdmin has already been created"
  else
    yes | gcloud iam roles create customIAPAdmin --project="${PROJECT_ID}" \
      --file=custom_iap_brand_admin.yaml
  fi
  unset __customIapAdmin
}

check_exec_version() {
  EXECUTABLE_NAME="${1}"

  if ! "${EXECUTABLE_NAME}" --version 2>&1; then
    echo "[ERROR]: ${EXECUTABLE_NAME} command is not available, but it's needed. Make it available in PATH and try again. Terminating..."
    exit ${ERR_MISSING_DEPENDENCY}
  fi

  unset EXECUTABLE_NAME
}

check_mandatory_variable() {
  _VARIABLE_NAME=$1
  _ERROR_MESSAGE=$2
  _VARIABLE_VALUE="${!_VARIABLE_NAME:-}"
  if [ -z "${_VARIABLE_VALUE}" ]; then
    echo "[ERROR]: ${_VARIABLE_NAME} environment variable that points to ${_ERROR_MESSAGE} is not defined. Terminating..."
    exit ${ERR_VARIABLE_NOT_DEFINED}
  fi
  unset _VARIABLE_NAME
  unset _ERROR_MESSAGE
  unset _VARIABLE_VALUE
}

check_and_set_persona(){
  __persona_name=$1
  __persona_value="${!__persona_name:-}"

  if [ -z "${__persona_value}" ]; then

    echo "$__persona_name is not set, skipping the role grants for this persona"
  else
    # pass the principal and and filename of roles
    enable_persona_roles $__persona_value "persona_roles_$__persona_name.txt"
  fi
}

create_service_account_and_enable_impersonation() {
  if [ -z "${SERVICE_ACCOUNT_ID:-}" ]; then
    export SERVICE_ACCOUNT_ID="deployer@$PROJECT_ID.iam.gserviceaccount.com"
    echo "using default name 'deployer' for SERVICE_ACCOUNT_ID"
  fi
  set +e # Disable errexit
  __deployer_sa=$(gcloud iam service-accounts list --format="value(email)" | grep "$SERVICE_ACCOUNT_ID")
  set -e # Re-enable errexit
  if [[ $__deployer_sa ]]; then
    echo "$__deployer_sa has already been created"
  else
    gcloud iam service-accounts create deployer \
      --description="The service account used to deploy Enterprise Knowledge Solution resources" \
      --display-name="EKS deployer service account" \
      --project="$PROJECT_ID"
    sleep 10 # ocassional flaky errors that "sa does not exist" when trying to apply IAM roles immediately after creation
  fi
  enable_role "roles/iam.serviceAccountTokenCreator" "$ACTIVE_PRINCIPAL" "$SERVICE_ACCOUNT_ID"
  unset __deployer_sa
}

# shell script function to check if api is enabled
check_api_enabled() {
  local __api_endpoint=$1
  COUNTER=0
  MAX_TRIES=100
  while ! gcloud services list --project="$PROJECT_ID" | grep -i "$__api_endpoint" && [ $COUNTER -lt $MAX_TRIES ]; do
    sleep 6
    printf "."
    COUNTER=$((COUNTER + 1))
  done
  if [ $COUNTER -eq $MAX_TRIES ]; then
    echo "${__api_endpoint} api is not enabled, installation can not continue!"
    exit 1
  else
    echo "${__api_endpoint} api is enabled"
  fi
  unset __api_endpoint
}

# shell script function to enable api
enable_api() {
  local __api_endpoint=$1
  gcloud services enable "$__api_endpoint" --project="$PROJECT_ID"
  check_api_enabled "$__api_endpoint"
  unset __api_endpoint
}

# enable all apis in the array
enable_bootstrap_apis() {
  readarray -t apis_array <project_apis.txt
  for i in "${apis_array[@]}"; do
    enable_api "$i"
  done
}

# shell script function to enable IAM roles
enable_role() {
  local __role=$1 __principal=$2 __resource=$3
  echo "granting IAM Role $__role to $__principal at resource $__resource "
  gcloud projects add-iam-policy-binding "$PROJECT_ID" --role="$__role" --member="$__principal" 1>/dev/null
  unset __role
  unset __principal
}

# enable all roles bundled into a persona, based on a textfile listing the roles
enable_persona_roles() {
  local __principal="$1"
  local __arrayfile=$2
  readarray -t roles_array <$__arrayfile
  for i in "${roles_array[@]}"; do
    enable_role "${i/\$\{PROJECT_ID\}/"$PROJECT_ID"}" "$__principal" "projects/$PROJECT_ID"
  done
  unset __principal
}

set_adc() {
  # check if the script is manually triggered by a user, or automated in CI build by a service account. Different methods of ADC for each
  if echo "$ACTIVE_PRINCIPAL" | grep "iam.gserviceaccount.com"; then
    echo "WARNING: Setting application default credentials with an impersonated service account requires an interactive sign-in flow with your username and password, but this script has been run with a service account identity. Ensure that you set ADC with the correct service account before running terraform commands. https://cloud.google.com/docs/authentication/provide-credentials-adc"

  else
    gcloud auth application-default login --impersonate-service-account="${SERVICE_ACCOUNT_ID}"
  fi
}
