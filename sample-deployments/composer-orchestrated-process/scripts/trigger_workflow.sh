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

# Just a small helper to your developers - a small bash function to trigger the DAG from the command line:

function trigger_dag() {

  json_config=$(
    cat <<EOF
  {
    "input_bucket": "docs-input-${PROJECT_ID}",
    "process_bucket": "dpu-process-${PROJECT_ID}",
    "input_folder": null,
    "supported_files": [
        {
            "file-suffix": "pdf",
            "processor": "agent-builder"
        },
        {
            "file-suffix": "txt",
            "processor": "agent-builder"
        },
        {
            "file-suffix": "html",
            "processor": "agent-builder"
        },
        {
            "file-suffix": "msg",
            "processor": "dpu-doc-processor"
        },
        {
            "file-suffix": "zip",
            "processor": "dpu-doc-processor"
        },
        {
            "file-suffix": "xlsx",
            "processor": "dpu-doc-processor"
        },
        {
            "file-suffix": "xlsm",
            "processor": "dpu-doc-processor"
        },
        {
            "file-suffix": "docx",
            "processor": "dpu-doc-processor"
        }
    ],
    "classifier": {
        "location": "${DOC_AI_REGION}",
        "processor_id": "${DOC_AI_PROCESSOR_ID}",
        "project_id": "${DOC_AI_PROJECT_ID}"
    }
}
EOF
  )
  # echo ${json_config}
  gcloud composer environments run dpu-composer --location "${COMPOSER_LOCATION}" dags trigger -- -c "${json_config}" run_docs_processing
}

set -o errexit
set -o nounset

# shellcheck source=/dev/null
. scripts/common.sh

# Check if PROJECT_ID is set, otherwise prompt for input
if [[ -z "${PROJECT_ID:-}" ]]; then
  read -r -p "Enter PROJECT_ID: " PROJECT_ID
else
  echo "PROJECT_ID is set to: $PROJECT_ID"
fi
[[ -z "$PROJECT_ID" ]] && echo "PROJECT_ID is required." && exit 1

# Check if DOC_AI_PROJECT_ID is set, otherwise prompt for input
if [[ -z "${DOC_AI_PROJECT_ID:-}" ]]; then
  read -r -p "Enter DOC_AI_PROJECT_ID: " DOC_AI_PROJECT_ID
else
  echo "DOC_AI_PROJECT_ID is set to: $DOC_AI_PROJECT_ID"
fi
[[ -z "$DOC_AI_PROJECT_ID" ]] && echo "DOC_AI_PROJECT_ID is required." && exit 1

# Check if DOC_AI_REGION is set, otherwise prompt for input
if [[ -z "${DOC_AI_REGION:-}" ]]; then
  read -r -p "Enter DOC_AI_REGION: " DOC_AI_REGION
else
  echo "DOC_AI_REGION is set to: $DOC_AI_REGION"
fi
[[ -z "$DOC_AI_REGION" ]] && echo "DOC_AI_REGION is required." && exit 1

# Check if Composer Location is set, otherwise prompt for input
if [[ -z "${COMPOSER_LOCATION:-}" ]]; then
  read -r -p "Enter Composer Location: " COMPOSER_LOCATION
else
  echo "Composer Location is set to: $COMPOSER_LOCATION"
fi
[[ -z "$COMPOSER_LOCATION" ]] && echo "Composer Location is required." && exit 1

# Check if DOC_AI_PROCESSOR_ID is set, otherwise prompt for input
if [[ -z "${DOC_AI_PROCESSOR_ID:-}" ]]; then
  read -r -p "Enter DOC_AI_PROCESSOR_ID: " DOC_AI_PROCESSOR_ID
else
  echo "DOC_AI_PROCESSOR_ID is set to: $DOC_AI_PROCESSOR_ID"
fi
[[ -z "$DOC_AI_PROCESSOR_ID" ]] && echo "DOC_AI_PROCESSOR_ID is required." && exit 1

section_open "Trigger DAG"
trigger_dag
section_close
