#!/bin/bash

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

# PROJECT_NUM="536170242658"
# AGENT_BUILDER_LOCATION="global"
# AGENT_BUILDER_DATA_STORE_ID="dpu-doc-store"

# Check if a search string is provided as an argument
if [ -z "$1" ]; then
  echo "Error: Search string is required as an argument." >&2
  exit 1
fi

# Check if PROJECT_ID is set, otherwise prompt for input
if [[ -z "$PROJECT_ID" ]]; then
  read -r -p "Enter PROJECT_ID: " PROJECT_ID
else
  echo "PROJECT_ID is set to: $PROJECT_ID"
fi
[[ -z "$PROJECT_ID" ]] && echo "PROJECT_ID is required." && exit 1

PROJECT_NUM=$(gcloud projects list | grep "${PROJECT_ID}" | awk '{print $3}')

# Check if Agent Builder Datastore location/region is set, otherwise prompt for input
if [[ -z "$AGENT_BUILDER_LOCATION" ]]; then
  read -r -p "Enter Agent Builder Datastore location/region: " AGENT_BUILDER_LOCATION
else
  echo "Agent Builder Datastore location/region is set to: $AGENT_BUILDER_LOCATION"
fi
[[ -z "$AGENT_BUILDER_LOCATION" ]] && echo "Agent Builder Datastore location/region is required." && exit 1

# Check if Agent Builder Datastore ID is set, otherwise prompt for input
if [[ -z "$AGENT_BUILDER_DATA_STORE_ID" ]]; then
  read -r -p "Enter Agent Builder Datastore ID: " AGENT_BUILDER_DATA_STORE_ID
else
  echo "Agent Builder Datastore ID is set to: $AGENT_BUILDER_DATA_STORE_ID"
fi
[[ -z "$AGENT_BUILDER_DATA_STORE_ID" ]] && echo "Agent Builder Datastore ID is required." && exit 1

# Check if a search string is provided as an argument
if [ -z "$1" ]; then
  echo "Error: Search string is required as an argument." >&2
  exit 1
fi

# Set the string to search for from the first argument
search_string="$1"

# Run the curl command and pipe the output to grep
curl -X GET \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "x-goog-user-project: $PROJECT_NUM" \
  "https://discoveryengine.googleapis.com/v1alpha/projects/$PROJECT_NUM/locations/$AGENT_BUILDER_LOCATION/collections/default_collection/dataStores/$AGENT_BUILDER_DATA_STORE_ID/branches/default_branch/documents" | grep "$search_string"
