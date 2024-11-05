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

import logging
import os
from enum import Enum
from typing import Any, Dict, Tuple, Set

from google.cloud import documentai, storage


class FolderNames(str, Enum):
    PDF_GENERAL = "pdf"
    CLASSIFICATION_RESULTS = "classified_pdfs_results"


def get_process_job_params(
    bq_table,
    doc_processor_job_name,
    gcs_reject_bucket,
    mv_params,
    supported_files: Dict[str, str],
    timeout: int = 600
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


def read_classifier_job_output(
    process_bucket: str,
    process_folder: str,
    known_labels: list[str],
    threshold: float = 0.7,
) -> Set[str]:
    """
    Method that will read the json output of the DocAI custom classifier, and move the classified files into their
    proper location. This method also returns a set of labels that were detected, in order to enable filtering later
    on which processors need to be activated.
    Args:
        process_bucket: the name of the processing bucket
        process_folder: path in the bucket of the processing folder
        known_labels: list of possible labels configured by the classifier
        threshold: minimum threshold of confidence to be considered by the classifier in order to validate labels.

    Returns: set of detected labels

    """

    gcs_input_prefix = f"{process_folder}/{FolderNames.PDF_GENERAL.value}"

    storage_client = storage.Client()
    found_labels = set()

    # Get List of Document Objects from the Output Bucket
    prefix = f"{process_folder}/{FolderNames.CLASSIFICATION_RESULTS.value}"

    bucket = storage_client.get_bucket(process_bucket)
    output_blobs = bucket.list_blobs(prefix=prefix, match_glob="**/*.json")
    output_blobs = list(output_blobs)
    logging.info(
        f"Found {len(output_blobs)} under bucket {process_bucket} " f"with {prefix=}"
    )
    # Document AI may output multiple JSON files per source file
    # In fact, Output file name contains the original file name without the
    # extension
    # but also adds a dash and a sequential number in the filename (before the
    # .json extension), which can optionally be more then once - so we
    # need to gather all data from all related output json files and then
    # parse them
    original_filename_to_json_output_map: Dict[str, Any] = {}

    for blob in output_blobs:
        # Document AI should only output JSON files to GCS
        if blob.content_type != "application/json":
            logging.info(
                f"Skipping non-supported file: {blob.name} - Mimetype: "
                f"{blob.content_type}"
            )
            continue

        # Download JSON File as bytes object and convert to Document Object
        document = documentai.Document.from_json(
            blob.download_as_bytes(), ignore_unknown_fields=True
        )

        # For a full list of Document object attributes, please reference
        # this page:
        # https://cloud.google.com/python/docs/reference/documentai/latest
        # /google.cloud.documentai_v1.types.Document

        # assuming the original file was a PDF, reconstruct the original
        # filename and put into the collected map the entities found
        original_with_suffix_basename = os.path.basename(blob.name).split(".json")[0]
        output_file_name_split_dashes = original_with_suffix_basename.split("-")[:-1]
        original_filename = "-".join(output_file_name_split_dashes) + ".pdf"
        full_original_file_name = f"{gcs_input_prefix}/{original_filename}"
        logging.info(f"reading results for file {full_original_file_name}")
        if full_original_file_name not in original_filename_to_json_output_map:
            original_filename_to_json_output_map[full_original_file_name] = []

        original_filename_to_json_output_map[full_original_file_name].extend(
            document.entities
        )

    # Now that we covered all json output and collected data into our map,
    # we can loop over the map and make the final decision for each file
    for original_blob_path, entities in original_filename_to_json_output_map.items():
        # Take the classified entities
        # 1. filter out any unknown labels
        # 2. filter out any labels that are under the threshold confidence level
        # 3. sort the remaining labels according to the confidence level
        # 4. convert the label to a lower case
        sorted_entities_type_but_only_above_threshold = list(
            map(
                lambda e: e.type.strip().lower(),
                sorted(
                    filter(
                        lambda e: e.confidence > threshold,
                        filter(
                            lambda e: e.type.strip().lower() in known_labels, entities
                        ),
                    ),
                    key=lambda e: e.confidence,
                    reverse=True,
                ),
            )
        )

        # this will check if we have any labels left after filtering - if no
        # label made it past the threshold, then we will treat this document
        # as a "general" document.
        if not sorted_entities_type_but_only_above_threshold:
            # classification_dict[full_original_file_name] = "general"
            # In most cases, we would classify this document as "general",
            # but since the next step would be to copy classified files to a
            # different directory for different handling, we actually want to
            # take the unclassified documents (general) and keep them in
            # place, so the easiest solution is to just remove them from this
            # output.
            logging.info(
                f"{original_blob_path} was not detected to be of a specific type."
            )
            continue

        # if we do have some labels after filtering, we will take the
        # first one, since the labels were also sorted, so we will use
        # the highest confidence label.
        chosen_label = sorted_entities_type_but_only_above_threshold[0]
        found_labels.add(chosen_label)

        original_filename = os.path.basename(original_blob_path)
        source_blob = bucket.blob(original_blob_path)
        destination_blob = (
            f"{process_folder}/pdf-{chosen_label}/input/{original_filename}"
        )
        logging.info(f"{original_blob_path} was detected to be a '{chosen_label}'. Moving to {destination_blob}")
        bucket.copy_blob(
            blob=source_blob,
            destination_bucket=bucket,
            new_name=destination_blob,
        )
        logging.info(f"Copied {source_blob.name} to {destination_blob}")
        bucket.delete_blob(original_blob_path)
        logging.info(f"Deleted original file {original_blob_path}")

    return found_labels


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
