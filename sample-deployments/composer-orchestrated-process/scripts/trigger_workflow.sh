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

PARENT_DIR="$(dirname "$0")/.."

function trigger_dag() {
  # read terraform state
  outputs=$(terraform output -json -chdir="$PARENT_DIR/../")

  json_config=$(
    cat <<EOF
  {
    "input_bucket": "$(echo "$outputs" | jq -r ".gcs_input_bucket_name.value")",
    "process_bucket": "$(echo "$outputs" | jq -r ".gcs_process_bucket_name.value")",
    "input_folder": null,
    "supported_files": [
        {
            "file-suffix": "pdf",
            "processor": "txt-processor"
        },
        {
            "file-suffix": "txt",
            "processor": "txt-processor"
        },
        {
            "file-suffix": "html",
            "processor": "txt-processor"
        },
        {
            "file-suffix": "msg",
            "processor": "msg-processor"
        },
        {
            "file-suffix": "zip",
            "processor": "zip-processor"
        },
        {
            "file-suffix": "xlsx",
            "processor": "xlsx-processor"
        },
        {
            "file-suffix": "xlsm",
            "processor": "xlsx-processor"
        },
        {
            "file-suffix": "docx",
            "processor": "txt-processor"
        }
    ],
    "classifier": "$(echo "$outputs" | jq -r ".classifier_processor_id.value")",
    "doc-ai-processors" : $(echo "$outputs" | jq -r ".specialized_processors_ids_json.value | to_entries | map({label: .key, \"doc-ai-processor-id\": .value})")
}
EOF
  )
  echo $json_config
  gcloud composer environments run dpu-composer --location "$(echo "$outputs" | jq -r ".composer_location.value")" dags trigger -- -c "${json_config}" run_docs_processing
}

set -o errexit
set -o nounset
set -x

# shellcheck source=/dev/null
. "$(dirname "$0")/common.sh"

section_open "Trigger DAG"
echo $(terraform output -json -chdir="$PARENT_DIR/../")
trigger_dag
section_close
