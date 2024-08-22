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
  echo "Usage: $0 [-d <DOC_ID> -u <DOC_URI> -t <BQ_TABLE> -l <LOCATION> [-p <PROJECT_ID>]] | [-b <BATCH_ID> -l <LOCATION> [-p <PROJECT_ID>]]"
  echo "  -l LOCATION   Data Store location (global, us, or eu)"
  echo "  -p PROJECT_ID (Optional) Google Cloud Project ID (defaults to gcloud config)"
  echo "Single document deletion:"
  echo "  -d DOC_ID     Document ID from Agent Builder Datastore"
  echo "  -u DOC_URI    Document URI from Agent Builder Datastore"
  echo "  -t BQ_TABLE   BigQuery table containing document metadata"
  echo "Batch deletion:"
  echo "  -b BATCH_ID   Batch ID to identify BigQuery processing table and GCS folder"
  exit 1
}

# Process command line arguments
while getopts ":d:u:t:b:p:l:" opt; do
  case "${opt}" in
    d) 
      DOC_ID=${OPTARG} ;;
    u) 
      DOC_URI=${OPTARG} ;;
    t) 
      BQ_TABLE=${OPTARG} ;;
    b)
      BATCH_ID=${OPTARG} ;;
    p) 
      PROJECT_ID=${OPTARG} ;;
    l)
      LOCATION=${OPTARG} ;;
    \?) 
      echo "Invalid option: -${OPTARG}" >&2; usage ;;
    :) 
      echo "Option -${OPTARG} requires an argument." >&2; usage ;;
  esac
done

shift $((OPTIND-1))

DOC_ID=${DOC_ID:-}
DOC_URI=${DOC_URI:-}
BQ_TABLE=${BQ_TABLE:-}
LOCATION=${LOCATION:-}

# Determine the deletion mode
if [ -n "${DOC_ID}" ] || [ -n "${DOC_URI}" ] || [ -n "${BQ_TABLE}" ]; then
  # Check if required arguments are provided
  if [ -z "${DOC_ID}" ] || [ -z "${DOC_URI}" ] || [ -z "${BQ_TABLE}" ] || [ -z "${LOCATION}" ]; then
    echo "Error: Missing required arguments." >&2
    usage
  fi
  MODE="single"
elif [ -n "${BATCH_ID}" ]; then
  # Check if required arguments are provided
  if [ -z "${LOCATION}" ]; then
    echo "Error: Missing required arguments for batch deletion." >&2
    usage
  fi
  MODE="batch"
else
  echo "Error: You must provide arguments for either single document or batch deletion." >&2
  usage
fi

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

if [ "$MODE" = "single" ]; then
  # Confirmation prompt
  read -r -p "You are about to delete document with ID '$DOC_ID' from project '$PROJECT_ID'. Are you sure? [y/N] " response
  if [[ ! "$response" =~ ^[yY]$ ]]; then
    echo "Aborting deletion."
    exit 0
  fi

  # Construct Agent Builder Datastore deletion URI
  DELETE_URI="${API_ENDPOINT}/v1alpha/projects/${PROJECT_ID}/locations/${LOCATION}/collections/default_collection/dataStores/dpu-doc-store/branches/default_branch/documents/${DOC_ID}"

  # EXECUTE THE FOLLOWING curl COMMAND to Delete document from Agent Builder Datastore
  curl -X DELETE \
    -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
    -H "x-goog-user-project: $PROJECT_ID" \
    "${DELETE_URI}"

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

elif [ "$MODE" = "batch" ]; then
  # Derive BigQuery table name from batch ID
  BQ_TABLE="docs_store.docs_processing_${BATCH_ID//-/_}"
  # Confirmation prompt
  read -r -p "You are about to delete documents associated with batch ID '$BATCH_ID' from project '$PROJECT_ID'. Are you sure? [y/N] " response
  if [[ ! "$response" =~ ^[yY]$ ]]; then
    echo "Aborting deletion."
    exit 0
  fi
  # Fetch document IDs and URIs from BigQuery
  QUERY="SELECT id, content.uri FROM \`$BQ_TABLE\`;"
  RESULTS=$(bq query --use_legacy_sql=false --format=sparse --project_id="$PROJECT_ID" "$QUERY" | awk 'NR>2')
  # Iterate through results and delete documents from Datastore and GCS
  while read -r line; do
    DOC_ID=$(echo "$line" | awk '{print $1}')
    DOC_URI=$(echo "$line" | awk '{$1 = ""; sub(/^ /, "", $0); print $0}')

    DELETE_URI="${API_ENDPOINT}/v1alpha/projects/${PROJECT_ID}/locations/${LOCATION}/collections/default_collection/dataStores/dpu-doc-store/branches/default_branch/documents/${DOC_ID}"

    curl -X DELETE \
      -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
      -H "x-goog-user-project: $PROJECT_ID" \
      "${DELETE_URI}"

    gsutil rm -r "$DOC_URI"
    gsutil rm -r "$DOC_URI".json

    bq query --use_legacy_sql=false --project_id="$PROJECT_ID" \
    "DELETE FROM \`$BQ_TABLE\` WHERE id = '$DOC_ID'"

    echo "Document with ID '$DOC_ID' successfully deleted from DP&U."
  done <<< "$RESULTS"

  bq rm --project_id="$PROJECT_ID" --headless=true -f -t "$BQ_TABLE"

  # Delete the GCS folder associated with the batch ID
  GCS_FOLDER="gs://dpu-process-${PROJECT_ID}/docs-processing-${BATCH_ID}"
  gsutil rm -r "$GCS_FOLDER"

  echo "Batch deletion for ID '$BATCH_ID' completed."
fi