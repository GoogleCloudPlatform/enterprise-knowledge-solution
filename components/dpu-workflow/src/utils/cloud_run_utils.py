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
import re

from google.cloud import storage, documentai

def get_process_job_params(bq_table, doc_processor_job_name, gcs_reject_bucket,
                           mv_params):
    process_job_params = []
    for mv_obj in mv_params:
        dest = (f"gs://{mv_obj['destination_bucket']}/"
                f"{mv_obj['destination_object']}")
        reject_dest = (f"gs://{gcs_reject_bucket}/"
                       f"{mv_obj['destination_object']}")
        bq_id = (f"{bq_table['project_id']}.{bq_table['dataset_id']}."
                 f"{bq_table['table_id']}")
        job_param = {
            "overrides": {
                "container_overrides": [
                    {
                        "name":       f"{doc_processor_job_name}",
                        "args":       [
                            dest,
                            reject_dest,
                            "--write_json=False",
                            f"--write_bigquery={bq_id}",
                        ],
                        "clear_args": False,
                    }
                ],
                "task_count":          1,
                "timeout":             "300s",
            }
        }
        process_job_params.append(job_param)
    return process_job_params



def forms_parser_job_params(bq_table, process_bucket, process_folder):
    bq_table_id = f"{bq_table['project_id']}.{bq_table['dataset_id']}.{bq_table['table_id']}"
    gcs_input_prefix = f"gs://{process_bucket}/{process_folder}/pdf-forms/input/"
    gcs_output_prefix = f"gs://{process_bucket}/{process_folder}/pdf-forms/output/"

    return {
        "overrides": {
            "container_overrides": [
                {
                    "env": [
                        {"name": "BQ_TABLE_ID", "value": bq_table_id},
                        {"name": "GCS_INPUT_PREFIX", "value": gcs_input_prefix},
                        {"name": "GCS_OUTPUT_PREFIX", "value":
                            gcs_output_prefix},
                    ]
                }
            ],
                "task_count": 1,
                "timeout": "300s",
            }
    }

def get_doc_classifier_job_overrides(
        classifier_project_id: str,
        classifier_location: str,
        classifier_processor_id: str,
        gcs_input_prefix: str,
        gcs_output_uri: str,
        timeout_in_seconds: int = 300,
):
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

def read_classifier_job_output(
    gcs_processing_bucket: str,
    gcs_output_path: str, # e.g.: "process_folder/pdf_classifier_output/"
    gcs_input_prefix: str, # e.g. "gs://process_bucket/process_folder/pdf/"
    threshold: float = 0.7,
) -> dict:

    # Once the operation is complete,
    # get output document information from operation metadata

    storage_client = storage.Client()

    classification_dict = {}

    # Get List of Document Objects from the Output Bucket
    output_blobs = storage_client.list_blobs(
        gcs_processing_bucket, prefix=gcs_output_path)

    # Document AI may output multiple JSON files per source file
    for blob in output_blobs:
        # Document AI should only output JSON files to GCS
        if blob.content_type != "application/json":
            print(
                f"Skipping non-supported file: {blob.name} - Mimetype: {blob.content_type}"
            )
            continue

        # Download JSON File as bytes object and convert to Document Object
        document = documentai.Document.from_json(
            blob.download_as_bytes(), ignore_unknown_fields=True
        )

        # For a full list of Document object attributes, please reference this page:
        # https://cloud.google.com/python/docs/reference/documentai/latest/google.cloud.documentai_v1.types.Document

        # assuming the original file was a PDF!!
        expression = r'([^/]+)$'
        file_name = re.search(expression, blob.name)
        output_file_name = file_name.group(1) #pyright: ignore[reportOptionalMemberAccess]
        orig_file_name = output_file_name.replace(".json", ".pdf", 1)
        full_original_file_name = gcs_input_prefix + orig_file_name
        sorted_entities = sorted(document.entities, key=lambda e:
        e.confidence, reverse=True)
        sorted_entities_type_but_only_above_threshold = list(
            map(lambda e: e.type.lower(),
                filter(lambda e: e.confidence > threshold,
                sorted_entities)
            )
        )
        if not sorted_entities_type_but_only_above_threshold:
            classification_dict[full_original_file_name] = "general"
        else:
            classification_dict[full_original_file_name] = (
                sorted_entities_type_but_only_above_threshold)[0]

    return classification_dict
