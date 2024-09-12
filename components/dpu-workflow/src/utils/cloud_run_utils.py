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

from google.cloud import storage, documentai


class FolderNames(str, Enum):
    PDF_FORMS_INPUT = "pdf-form/input/"
    PDF_FORMS_OUTPUT = "pdf-form/output/"
    PDF_GENERAL = "pdf"
    CLASSIFICATION_RESULTS = "classified_pdfs_results"


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


def __build_gcs_path__(bucket: str, folder: str, folder_name: FolderNames):
    return f"gs://{bucket}/{folder}/{folder_name.value}"


def forms_parser_job_params(bq_table, process_bucket, process_folder):
    bq_table_id = f"{bq_table['project_id']}.{bq_table['dataset_id']}.{bq_table['table_id']}"
    gcs_input_prefix = __build_gcs_path__(process_bucket, process_folder, FolderNames.PDF_FORMS_INPUT)
    gcs_output_prefix = __build_gcs_path__(process_bucket, process_folder,
                                         FolderNames.PDF_FORMS_OUTPUT)

    return {
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


def get_doc_classifier_job_overrides(
        classifier_project_id: str,
        classifier_location: str,
        classifier_processor_id: str,
        process_folder: str,
        process_bucket: str,
        timeout_in_seconds: int = 3000,
):
    gcs_input_prefix = __build_gcs_path__(process_bucket, process_folder,
                                          FolderNames.PDF_GENERAL)
    gcs_output_uri = __build_gcs_path__(process_bucket, process_folder,
                                        FolderNames.CLASSIFICATION_RESULTS)
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
) -> list:

    gcs_input_prefix = f"{process_folder}/{FolderNames.PDF_GENERAL.value}"


    storage_client = storage.Client()
    classification_mv_params = []

    # Get List of Document Objects from the Output Bucket
    prefix = f"{process_folder}/{FolderNames.CLASSIFICATION_RESULTS.value}"

    bucket = storage_client.get_bucket(process_bucket)
    output_blobs = bucket.list_blobs(
        prefix=prefix,
        match_glob="**/*.json"
    )
    output_blobs = list(output_blobs)
    logging.info(f"Found {len(output_blobs)} under bucket {process_bucket} "
                 f"with {prefix=}")
    # Document AI may output multiple JSON files per source file
    # In fact, Output file name contains the original file name without the extension
    # but also adds a dash and a sequential number in the filename (before the
    # .json extension), which can optionally be more then once - so we
    # need to gather all data from all related output json files and then
    # parse them
    original_filename_to_json_output_map = {}

    for blob in output_blobs:
        # Document AI should only output JSON files to GCS
        if blob.content_type != "application/json":
            logging.info(
                f"Skipping non-supported file: {blob.name} - Mimetype: {blob.content_type}"
            )
            continue

        # Download JSON File as bytes object and convert to Document Object
        document = documentai.Document.from_json(
            blob.download_as_bytes(), ignore_unknown_fields=True
        )

        # For a full list of Document object attributes, please reference this page:
        # https://cloud.google.com/python/docs/reference/documentai/latest/google.cloud.documentai_v1.types.Document

        # assuming the original file was a PDF, reconstruct the original
        # filename and put into the collected map the entities found
        original_with_suffix_basename = os.path.basename(blob.name).split(".json")[
            0]
        output_file_name_split_dashes = original_with_suffix_basename.split(
            "-")[:-1]
        original_filename = "-".join(output_file_name_split_dashes) + ".pdf"
        full_original_file_name = f"{gcs_input_prefix}/{original_filename}"
        logging.info(f"reading results for file {full_original_file_name}")
        if full_original_file_name not in original_filename_to_json_output_map:
            original_filename_to_json_output_map[full_original_file_name] = []

        original_filename_to_json_output_map[full_original_file_name].extend(
            document.entities)

    # Now that we covered all json output and collected data into our map,
    # we can loop over the map and make the final decision for each file
    for original_blob_path, entities in (
            original_filename_to_json_output_map.items()):
        # Take the classified entities
        # 1. filter out any unknown labels
        # 2. filter out any labels that are under the threshold confidence level
        # 3. sort the remaining labels according to the confidence level
        # 4. convert the label to a lower case
        sorted_entities_type_but_only_above_threshold = list(
            map(lambda e: e.type.strip().lower(),
                sorted(
                    filter(
                        lambda e: e.confidence > threshold,
                        filter(lambda e: e.type.strip().lower() in known_labels,
                            entities
                        )
                    ), key=lambda e: e.confidence, reverse=True
                )
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
            logging.info(f"{original_blob_path} was not detected to be "
                         f"of a specific type.")
            continue

        # if we do have some labels after filtering, we will take the
        # first one, since the labels were also sorted, so we will use
        # the highest confidence label.
        chosen_label = sorted_entities_type_but_only_above_threshold[0]
        logging.info(f"{original_blob_path} was detected to be "
                         f"a '{chosen_label}'.")
        original_filename = os.path.basename(original_blob_path)
        # prepare mv operation parameters, that will be used in the next step.
        parameter_obj = {
            "source_object":      original_blob_path,
            "destination_bucket": process_bucket,
            "destination_object": f"{process_folder}/pdf-{chosen_label}/"
                                  f"{original_filename}",
        }
        source_blob = bucket.blob(original_blob_path)
        destination_blob = (f"{process_folder}/pdf-{chosen_label}/"
                            f"input/{original_filename}")
        bucket.copy_blob(
            blob=source_blob,
            destination_bucket=bucket,
            new_name=destination_blob,
        )
        logging.info(f"Copied {source_blob.name} to {destination_blob}")
        bucket.delete_blob(original_blob_path)
        logging.info(f"Deleted original file {original_blob_path}")
        classification_mv_params.append(parameter_obj)

    return classification_mv_params
