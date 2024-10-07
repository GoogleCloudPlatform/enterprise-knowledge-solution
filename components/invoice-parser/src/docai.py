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
import re
from typing import List

from google.api_core.client_options import ClientOptions
from google.api_core.exceptions import RetryError, GoogleAPICallError
from google.api_core.gapic_v1.client_info import ClientInfo
from google.api_core.operation import Operation
from google.cloud import storage, documentai
from google.cloud.documentai_v1 import BatchProcessMetadata
from google.cloud.exceptions import InternalServerError

from main import DetectedEntity, USER_AGENT


def call_batch_processor(
    project_id: str,
    location: str,
    processor_id: str,
    gcs_input_prefix: str,
    gcs_output_uri: str
) -> Operation:
    """
    Call the DocAI processor to start the long running batch operation.
    Args:
        project_id: The project ID where the DocAI processor is created
        location: the location of the DocAI processor
        processor_id: the processor ID
        gcs_input_prefix: GCS input prefix, where the input/source documents can be found.
        gcs_output_uri: GCS output, where to write the results of the processor

    Returns: The instance of the operation. 

    """
    opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
    client_info = ClientInfo(user_agent=USER_AGENT)
    client = documentai.DocumentProcessorServiceClient(client_options=opts, client_info=client_info)

    gcs_prefix = documentai.GcsPrefix(gcs_uri_prefix=gcs_input_prefix)
    input_config = documentai.BatchDocumentsInputConfig(gcs_prefix=gcs_prefix)

    gcs_output_config = documentai.DocumentOutputConfig.GcsOutputConfig(gcs_uri=gcs_output_uri)
    output_config = documentai.DocumentOutputConfig(gcs_output_config=gcs_output_config)

    processor_name = client.processor_path(project_id, location, processor_id)
    request = documentai.BatchProcessRequest(
        name=processor_name,
        input_documents=input_config,
        document_output_config=output_config,
    )
    operation: Operation = client.batch_process_documents(request)
    logging.info(f"Started batch process; {operation.metadata=};")
    return operation


def wait_for_completion_and_verify_success(
    batch_operation: Operation,
    timeout=1000
) -> List[BatchProcessMetadata.IndividualProcessStatus]:
    try:
        logging.info(
            f"Waiting for operation {batch_operation.operation.name} to complete..."
        )
        batch_operation.result(timeout=timeout)
    # Catch exception when operation doesn't finish before timeout
    except (RetryError, InternalServerError, GoogleAPICallError) as e:
        logging.error(e.message)
        raise e
    logging.info("Batch Process Finished. Checking Status")
    metadata = documentai.BatchProcessMetadata(batch_operation.metadata)

    if metadata.state != documentai.BatchProcessMetadata.State.SUCCEEDED:
        raise ValueError(f"Batch Process Failed: {metadata.state_message}")
    logging.info("Batch process has succeeded")

    return list(metadata.individual_process_statuses)


def read_and_parse_batch_results(
    storage_client: storage.Client,
    individual_process_statuses: List[BatchProcessMetadata.IndividualProcessStatus],
    gcs_input_prefix: str,
    run_id: str
) -> List[DetectedEntity]:
    output_rows: List[DetectedEntity] = []
    for process in individual_process_statuses:
        matches = re.match(r"gs://(.*?)/(.*)", process.output_gcs_destination)
        if not matches:
            logging.error(
                "Could not parse output GCS destination:",
                process.output_gcs_destination,
            )
            continue

        # Get List of Document Objects from the Output Bucket
        output_bucket, output_prefix = matches.groups()
        output_blobs = storage_client.list_blobs(output_bucket, prefix=output_prefix)

        for blob in output_blobs:
            # Document AI should only output JSON files to GCS
            if blob.content_type != "application/json":
                logging.warning(
                    f"Skipping non-supported file: {blob.name} - Mimetype: {blob.content_type}"
                )
                continue

            # Read the text recognition output from the processor and create a BQ table row
            document = documentai.Document.from_json(
                blob.download_as_bytes(),
                ignore_unknown_fields=True,
            )

            original_filename = (blob.name.rsplit("-", 1)[0]).rsplit("/", 1)[1]
            original_file_path = f"{gcs_input_prefix}{original_filename}.pdf"

            # Grab each key/value pair and their corresponding confidence scores.
            for entity in document.entities:
                output_rows.append(DetectedEntity(
                    results_file=f"gs://{output_bucket}/{blob.name}",
                    entity_type=entity.type,
                    original_filename=original_file_path,
                    raw_text=entity.mention_text,
                    normalized_text=entity.normalized_value.text,
                    confidence=entity.confidence,
                    run_id=run_id,
                ))
                # Get Properties (Sub-Entities) with confidence scores
                for prop in entity.properties:
                    output_rows.append(DetectedEntity(
                        results_file=f"gs://{output_bucket}/{blob.name}",
                        entity_type=prop.type,
                        original_filename=original_file_path,
                        raw_text=prop.mention_text,
                        normalized_text=prop.normalized_value.text,
                        confidence=prop.confidence,
                        run_id=run_id,
                    ))

    return output_rows
