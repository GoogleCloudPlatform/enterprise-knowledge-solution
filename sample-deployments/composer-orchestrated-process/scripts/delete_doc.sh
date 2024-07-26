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

# Function to print usage instructions
usage() {
  echo "Usage: $0 -d <DOC_ID> -u <DOC_URI> -t <BQ_TABLE> [-p <PROJECT_ID>]"
  echo "  -d DOC_ID     Document ID from Agent Builder Datastore"
  echo "  -u DOC_URI    Document URI from Agent Builder Datastore"
  echo "  -t BQ_TABLE   BigQuery table containing document metadata"
  echo "  -p PROJECT_ID (Optional) Google Cloud Project ID (defaults to gcloud config)"
  exit 1
}

# Process command line arguments
while getopts ":d:u:t:p:" opt; do
  case "${opt}" in
    d) 
      DOC_ID=${OPTARG} ;;
    u) 
      DOC_URI=${OPTARG} ;;
    t) 
      BQ_TABLE=${OPTARG} ;;
    p) 
      PROJECT_ID=${OPTARG} ;;
    \?) 
      echo "Invalid option: -${OPTARG}" >&2; usage ;;
    :) 
      echo "Option -${OPTARG} requires an argument." >&2; usage ;;
  esac
done

shift $((OPTIND-1))

# Check if required arguments are provided
if [ -z "${DOC_ID}" ] || [ -z "${DOC_URI}" ] || [ -z "${BQ_TABLE}" ]; then
  echo "Error: Missing required arguments." >&2
  usage
fi

# Set default project ID if not provided
if [ -z "$PROJECT_ID" ]; then
  PROJECT_ID=$(gcloud config get-value project)
fi

# Confirmation prompt
read -r -p "You are about to delete document with ID '$DOC_ID' from project '$PROJECT_ID'. Are you sure? [y/N] " response
if [[ ! "$response" =~ ^[yY]$ ]]; then
  echo "Aborting deletion."
  exit 0
fi

# EXECUTE THE FOLLOWING curl COMMAND to Delete document from Agent Builder Datastore
curl -X DELETE \
   -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
   -H "x-goog-user-project: $PROJECT_ID" \
  "https://discoveryengine.googleapis.com/v1alpha/projects/$PROJECT_ID/locations/global/collections/default_collection/dataStores/dpu-doc-store/branches/default_branch/documents/$DOC_ID"

# EXECUTE THE FOLLOWING bq COMMAND to Delete document meta-data from BigQuery Table
bq query --use_legacy_sql=false --project_id="$PROJECT_ID" \
  "DELETE FROM \`$BQ_TABLE\` WHERE id = '$DOC_ID'"

# EXECUTE THE FOLLOWING bq COMMAND to Delete the BigQuery Table containing the document meta-data
# BQ_TABLE="${BQ_TABLE/\./:}"
# bq rm -t "$BQ_TABLE"

# EXECUTE THE FOLLOWING gsutil COMMAND to Delete the document and meta-data from Google Cloud Storage Bucket
gsutil rm -r "$DOC_URI"
gsutil rm -r "$DOC_URI".json

# EXECUTE THE FOLLOWING gsutil COMMAND to Delete the folder containing the document and meta-data from Google Cloud Storage Bucket
# DOC_FOLDER=$(cut -d'/' -f1-4 <<< "$DOC_URI")
# gsutil rm -r $DOC_FOLDER

# Print success message
echo "Document with ID '$DOC_ID' successfully deleted from DP&U."