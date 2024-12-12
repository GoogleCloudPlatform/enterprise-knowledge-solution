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
  echo "Usage: $0  -m <MODE> -r <RUN_ID> [-d <DOC_ID>] [-f]"
  echo "  -m MODE       Mode of operation - must be 'single' or 'batch'. When 'single' is specified, a DOC_ID must be specified as well."
  echo "  -r RUN ID     Run ID - the suffix of the data table in bigquery, can be found in the GCS path or from the composer run. Format: dd-mm-yyyy-abcdefgh. hyphens and dashes are interchangable. e.g: 09_12_2024_xc252nz8 or 09-12-2024-xc252nz8"
  echo "  -d DOC_ID     Optional. Document ID from BigQuery Data table."
  echo "  -f FORCE      Optional. Skip confirmation prompt."
  exit 1
}

FORCE=0
RUN_ID=""
DOC_ID=""
MODE=""

# Process command line arguments
while getopts ":m:r:d:f" opt; do
  case "${opt}" in
  m)
    MODE=${OPTARG}
    ;;
  r)
    RUN_ID=${OPTARG}
    ;;
  d)
    DOC_ID=${OPTARG}
    ;;
  f)
    FORCE=1
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

shift $((OPTIND - 1))

if [[ -z "${MODE}" ]]; then
  echo "Error: -m MODE is a required argument." >&2
  usage
fi

if [[ -z "${RUN_ID}" ]]; then
  echo "Error: -r RUN_ID is a required argument." >&2
  usage
fi

# Verify mode is valid
case "$MODE" in
single)
  if [[ -z "${DOC_ID}" ]]; then
    echo "Error: DOC_ID must be specified when MODE is single."
    usage
  fi
  echo "Mode single selected with DOC_ID: ${DOC_ID}"
  ;;
batch)
  if [[ -n "${DOC_ID}" ]]; then
    echo "Error: DOC_ID should not be specified when MODE is batch."
    usage
  fi
  echo "Mode batch selected."
  ;;

*)
  echo "Error: Invalid mode. Must be 'single' or 'batch'."
  usage
  ;;
esac

# Ask for confirmation
if [[ $FORCE -eq 0 ]]; then # Check if force mode is disabled
  case "${MODE}" in
  single)
    read -r -p "Retype DOC_ID '${DOC_ID}' to confirm deletion: " typed_doc_id
    if [[ "${typed_doc_id}" != "$DOC_ID" ]]; then
      echo "DOC_ID mismatch. Aborting."
      exit 1
    fi
    ;;
  batch)
    read -r -p "Retype RUN_ID '${RUN_ID}' to confirm deletion: " typed_run_id
    if [[ "${typed_run_id}" != "${RUN_ID}" ]]; then
      echo "RUN_ID mismatch. Aborting."
      exit 1
    fi
    ;;
  esac
fi

echo "Executing 'gcloud run jobs execute delete-docs --update-env-vars=\"RUN_ID=${RUN_ID},DOC_ID=${DOC_ID},MODE=${MODE}\" --wait'"
gcloud run jobs execute delete-docs --update-env-vars="RUN_ID=$RUN_ID,DOC_ID=$DOC_ID,MODE=$MODE" --wait
result=$?

if [[ $result -ne 0 ]]; then
  read -r -p "Deletion job failed with exit code $result. Press Enter to exit."
  exit $result # Exit with the same code as the gcloud command
fi
echo "Deletion job finished successfully."
