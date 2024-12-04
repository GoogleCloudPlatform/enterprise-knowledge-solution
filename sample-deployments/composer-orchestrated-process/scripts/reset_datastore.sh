#!/usr/bin/env bash
# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


set -o errexit
set -o nounset

# Function to print usage instructions
usage() {
  echo "Usage: $0 [-l <LOCATION> [-p <PROJECT_ID>]]"
  echo "  -l LOCATION   Data Store location (global, us, or eu)"
  echo "  -p PROJECT_ID (Optional) Google Cloud Project ID (defaults to gcloud config)"
  exit 1
}

# Process command line arguments
while getopts ":p:l:" opt; do
  case "${opt}" in
  p)
    PROJECT_ID=${OPTARG}
    ;;
  l)
    LOCATION=${OPTARG}
    ;;
  \?)
    echo "Invalid option: -${OPTARG}" >&2
    usage
    ;;
  :)
    echo "Option -${OPTARG} requires an argument." >&2
    usage
    ;;
  esac
done

# Validate location argument
if [[ ! "$LOCATION" =~ ^(global|us|eu)$ ]]; then
  echo "Error: Invalid location. Must be 'global', 'us', or 'eu'." >&2
  usage
fi

# Set API endpoint based on location
if [ "$LOCATION" = "global" ]; then
  API_ENDPOINT="https://discoveryengine.googleapis.com"
else
  API_ENDPOINT="https://${LOCATION}-discoveryengine.googleapis.com"
fi

# Set default project ID if not provided
if [ -z "$PROJECT_ID" ]; then
  PROJECT_ID=$(gcloud config get-value project)
fi

# Get the access token
ACCESS_TOKEN=$(gcloud auth application-default print-access-token)

# Construct Agent Builder Datastore URI
DSTORE_URI="${API_ENDPOINT}/v1alpha/projects/${PROJECT_ID}/locations/${LOCATION}/collections/default_collection/dataStores/${AGENT_BUILDER_DATA_STORE_ID}/branches/default_branch/documents"

# Execute the curl command and store the result in a variable
response=$(curl -X GET \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "x-goog-user-project: $PROJECT_ID" \
  "${DSTORE_URI}")

# Print response
echo "Response: $response"

# Check if the response is empty
if [[ -z "$response" || "$response" == "{}" ]]; then
  echo "Datastore is empty. Nothing to delete."
  exit 1
fi

# Extract the desired information from the response
document_names=$(echo "$response" | jq -r '.documents[].name' | awk -F '/' '{print $NF}')
printf "%s\n" "${document_names}"

# Create an array from the extracted information
readarray -t document_list <<<"$document_names"

# Print the list (optional)
printf "%s\n" "${document_list[@]}"

# Confirmation prompt
read -r -p "You are about to delete all documents from project '$PROJECT_ID'. Are you sure? [y/N] " response
if [[ ! "$response" =~ ^[yY]$ ]]; then
  echo "Aborting deletion."
  exit 0
fi

# Iterate through the list
for DOC_ID in "${document_list[@]}"; do

  printf "You are about to delete document with ID %s from project %s" "$DOC_ID" "$PROJECT_ID"

  # Construct Agent Builder Datastore deletion URI
  DELETE_URI="${DSTORE_URI}/${DOC_ID}"

  # EXECUTE THE FOLLOWING curl COMMAND to Delete document from Agent Builder Datastore
  curl -X DELETE \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "x-goog-user-project: $PROJECT_ID" \
    "${DELETE_URI}"
done
