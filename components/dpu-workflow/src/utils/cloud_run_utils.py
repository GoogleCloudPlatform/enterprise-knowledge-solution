# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from enum import Enum
from typing import Any, Dict


class FolderNames(str, Enum):
    PDF_GENERAL = "pdf"
    CLASSIFICATION_RESULTS = "classified_pdfs_results"


def get_process_job_params(
    bq_table,
    doc_processor_job_name,
    gcs_reject_bucket,
    mv_params,
    supported_files: Dict[str, str],
    timeout: int = 600,
):
    process_job_params = []
    supported_files_args = [f"--file-type={k}:{v}" for k, v in supported_files.items()]

    for mv_obj in mv_params:
        dest = f"gs://{mv_obj['destination_bucket']}/" f"{mv_obj['destination_object']}"
        reject_dest = f"gs://{gcs_reject_bucket}/{mv_obj['destination_object']}"
        bq_id = (
            f"{bq_table['project_id']}.{bq_table['dataset_id']}."
            f"{bq_table['table_id']}"
        )
        args = [
            dest,
            reject_dest,
            "--write_json=False",
            f"--write_bigquery={bq_id}",
        ]
        args.extend(supported_files_args)
        job_param = {
            "overrides": {
                "container_overrides": [
                    {
                        "name": f"{doc_processor_job_name}",
                        "args": args,
                        "clear_args": False,
                    }
                ],
                "task_count": 1,
                "timeout": f"{timeout}s",
            }
        }
        process_job_params.append(job_param)
    return process_job_params


def __build_gcs_path__(bucket: str, folder: str, folder_name: FolderNames):
    return f"gs://{bucket}/{folder}/{folder_name.value}"


def specialized_parser_job_params(
    possible_processors: Dict[str, str],
    job_name: str,
    run_id: str,
    bq_table: dict,
    process_bucket: str,
    process_folder: str,
    timeout: int = 600,
):
    bq_table_id = (
        f"{bq_table['project_id']}.{bq_table['dataset_id']}.{bq_table['table_id']}"
    )
    parser_job_params = []
    for label, processor_id in possible_processors.items():
        # specialized_parser_job_name = f"{job_name}-{label}"
        gcs_input_prefix = f"gs://{process_bucket}/{process_folder}/pdf-{label}/input"
        gcs_output_prefix = f"gs://{process_bucket}/{process_folder}/pdf-{label}/output"
        job_param = {
            "overrides": {
                "container_overrides": [
                    {
                        "name": job_name,
                        "env": [
                            {"name": "RUN_ID", "value": run_id},
                            {"name": "PROCESSOR_ID", "value": processor_id},
                            {"name": "GCS_INPUT_PREFIX", "value": gcs_input_prefix},
                            {"name": "GCS_OUTPUT_URI", "value": gcs_output_prefix},
                            {"name": "BQ_TABLE", "value": bq_table_id},
                        ],
                        "clear_args": False,
                    }
                ],
                "task_count": 1,
                "timeout": f"{timeout}s",
            }
        }
        parser_job_params.append(job_param)
    return parser_job_params


def get_doc_classifier_job_overrides(
    classifier_project_id: str,
    classifier_location: str,
    classifier_processor_id: str,
    process_folder: str,
    process_bucket: str,
    timeout_in_seconds: int = 3000,
):
    gcs_input_prefix = __build_gcs_path__(
        process_bucket, process_folder, FolderNames.PDF_GENERAL
    )
    gcs_output_uri = __build_gcs_path__(
        process_bucket, process_folder, FolderNames.CLASSIFICATION_RESULTS
    )
    return {
        "container_overrides": [
            {
                "env": [
                    {"name": "PROJECT_ID", "value": classifier_project_id},
                    {"name": "LOCATION", "value": classifier_location},
                    {"name": "PROCESSOR_ID", "value": classifier_processor_id},
                    {"name": "GCS_INPUT_PREFIX", "value": gcs_input_prefix},
                    {"name": "GCS_OUTPUT_URI", "value": gcs_output_uri},
                ]
            }
        ],
        "task_count": 1,
        "timeout": f"{timeout_in_seconds}s",
    }


def get_doc_registry_duplicate_job_override(
    input_folder: str,
    output_folder: str,
    doc_registry_table: str = "",
    timeout_in_seconds: int = 3000,
):
    params: Dict[str, Any] = {
        "container_overrides": [
            {
                "env": [
                    {"name": "GCS_INPUT_FILE_BUCKET", "value": input_folder},
                    {"name": "GCS_IO_URI", "value": output_folder},
                ]
            }
        ],
        "task_count": 1,
        "timeout": f"{timeout_in_seconds}s",
    }
    if doc_registry_table:
        params["container_overrides"][0]["env"].append(
            {"name": "BQ_DOC_REGISTRY_TABLE", "value": doc_registry_table}
        )
    return params


def get_doc_registry_update_job_override(
    input_bq_table: str,
    output_folder: str,
    doc_registry_table: str = "",
    timeout_in_seconds: int = 3000,
):
    params: Dict[str, Any] = {
        "container_overrides": [
            {
                "env": [
                    {"name": "ADD_DOCS", "value": "true"},
                    {"name": "BQ_INGESTED_DOC_TABLE", "value": input_bq_table},
                    {"name": "GCS_IO_URI", "value": output_folder},
                ]
            }
        ],
        "task_count": 1,
        "timeout": f"{timeout_in_seconds}s",
    }
    if doc_registry_table:
        params["container_overrides"][0]["env"].append(
            {"name": "BQ_DOC_REGISTRY_TABLE", "value": doc_registry_table}
        )
    return params
