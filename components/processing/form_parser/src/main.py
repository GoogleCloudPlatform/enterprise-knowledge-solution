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

import os
from typing import Optional

from google.api_core.client_options import ClientOptions
from google.api_core.exceptions import InternalServerError, GoogleAPICallError
from google.api_core.exceptions import RetryError
from google.cloud import storage
from load_data_in_bigquery import *


# Retrieve Job-defined env vars
TASK_INDEX = os.getenv("CLOUD_RUN_TASK_INDEX", 0)
TASK_ATTEMPT = os.getenv("CLOUD_RUN_TASK_ATTEMPT", 0)
# Retrieve User-defined env vars
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION")  # Example: - "us"
PROCESSOR_ID = os.getenv("PROCESSOR_ID")  # Example: - ac27785bf4bee278
GCS_OUTPUT_PREFIX = os.getenv(
    "GCS_OUTPUT_PREFIX"
)  # Must end with a trailing slash `/`. Format: gs://bucket/directory/subdirectory/
GCS_INPUT_PREFIX = os.getenv(
    "GCS_INPUT_PREFIX"
)  # Example: - "gs://doc-ai-processor/input-forms/" # Format: gs://bucket/directory/
BQ_TABLE_ID = os.getenv(
    "BQ_TABLE_ID"
)  # Specify your table ID in the format 'your-project.your_dataset.your_table'


def batch_process_documents(
    project_id: str,
    location: str,
    processor_id: str,
    gcs_output_uri: str,
    gcs_input_prefix: str,
    field_mask: Optional[str] = None,
    timeout: int = 400,
) -> None:
    """Program that processes documents with forms stored in a GCS bucket and converts into JSON.

    Args:
        project_id: project id where solution is deployed,
        location: location of the form Document AI form processor,
        processor_id: Processor Id of Document AI form processor,
        gcs_output_uri: GCS directory to store the out json files,
        gcs_input_prefix: GCS directory to store input files to be processed
    """
    # Set the `api_endpoint` if you use a location other than "us".
    opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")

    client = documentai.DocumentProcessorServiceClient(client_options=opts)

    # Specify a GCS URI Prefix to process an entire directory
    gcs_prefix = documentai.GcsPrefix(gcs_uri_prefix=gcs_input_prefix)
    input_config = documentai.BatchDocumentsInputConfig(gcs_prefix=gcs_prefix)

    # Cloud Storage URI for the Output Directory
    gcs_output_config = documentai.DocumentOutputConfig.GcsOutputConfig(
        gcs_uri=gcs_output_uri, field_mask=field_mask
    )

    # Where to write results
    output_config = documentai.DocumentOutputConfig(gcs_output_config=gcs_output_config)

    # The full resource name of the processor, e.g.:
    # projects/{project_id}/locations/{location}/processors/{processor_id}
    name = client.processor_path(project_id, location, processor_id)

    request = documentai.BatchProcessRequest(
        name=name,
        input_documents=input_config,
        document_output_config=output_config,
    )

    try:
        # BatchProcess returns a Long Running Operation (LRO)
        operation = client.batch_process_documents(request)

        # Continually polls the operation until it is complete.
        # This could take some time for larger files
        # Format: projects/{project_id}/locations/{location}/operations/{operation_id}
        logging.info(f"Waiting for operation {operation.operation.name} to complete...")
        operation.result(timeout=timeout)
    # Catch exception when operation doesn't finish before timeout
    except (RetryError, InternalServerError, GoogleAPICallError) as e:
        logging.error(f"An error occurred during batch processing: {e}")
        return

    # Once the operation is complete,
    # get output document information from operation metadata
    metadata = documentai.BatchProcessMetadata(operation.metadata)

    if metadata.state != documentai.BatchProcessMetadata.State.SUCCEEDED:
        raise ValueError(f"Batch Process Failed: {metadata.state_message}")

    storage_client = storage.Client()

    logging.info("Output files:")

    rows_to_insert = []
    # One process per Input Document
    for process in list(metadata.individual_process_statuses):
        # output_gcs_destination format: gs://BUCKET/PREFIX/OPERATION_NUMBER/INPUT_FILE_NUMBER/
        # The Cloud Storage API requires the bucket name and URI prefix separately
        matches = re.match(r"gs://(.*?)/(.*)", process.output_gcs_destination)
        if not matches:
            logging.error(
                "Could not parse output GCS destination:",
                process.output_gcs_destination,
            )
            continue

        output_bucket, output_prefix = matches.groups()

        # Get List of Document Objects from the Output Bucket
        output_blobs = storage_client.list_blobs(output_bucket, prefix=output_prefix)

        # Document AI may output multiple JSON files per source file
        for blob in output_blobs:
            # Document AI should only output JSON files to GCS
            if blob.content_type != "application/json":
                logging.info(
                    f"Skipping non-supported file: {blob.name} - Mimetype: {blob.content_type}"
                )
                continue

            # Read the text recognition output from the processor and create a BQ table row
            row_to_insert = build_output_metadata(
                blob, storage_client, gcs_input_prefix, gcs_output_uri
            )
            # Append the row to the list
            rows_to_insert.append(row_to_insert)

    # Load list of all the rows generated in the loop in BigQuery
    print(f"Total rows: {len(rows_to_insert)}")
    print(rows_to_insert)
    logging.info(f"Total rows: {len(rows_to_insert)} rows to insert: {rows_to_insert}")
    load_rows_into_bigquery(rows_to_insert, BQ_TABLE_ID)
    print(f"BQ_TABLE_ID: {BQ_TABLE_ID}")
    print(f"GCS_INPUT_PREFIX: {GCS_INPUT_PREFIX}")
    print(f"GCS_OUTPUT_PREFIX: {GCS_OUTPUT_PREFIX}")


# Start script
if __name__ == "__main__":
    logging.info(f"Starting Task #{TASK_INDEX}, Attempt #{TASK_ATTEMPT}...")
    if (
        not PROJECT_ID
        or not LOCATION
        or not PROCESSOR_ID
        or not GCS_OUTPUT_PREFIX
        or not GCS_INPUT_PREFIX
    ):
        logging.error("Environment variables missing")
    else:
        batch_process_documents(
            project_id=PROJECT_ID,
            location=LOCATION,
            processor_id=PROCESSOR_ID,
            gcs_output_uri=GCS_OUTPUT_PREFIX,
            gcs_input_prefix=GCS_INPUT_PREFIX,
        )
        name = os.environ.get("NAME", "World")
    logging.info(f"Completed Task #{TASK_INDEX}.")
