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
import sys
from typing import Optional

from google.api_core.client_options import (
    ClientOptions,  # type: ignore # pylint: disable = no-name-in-module # pylint: disable = import-error
)
from google.api_core.exceptions import (
    InternalServerError,  # type: ignore # pylint: disable = no-name-in-module # pylint: disable = import-error
)
from google.api_core.exceptions import (
    RetryError,  # type: ignore # pylint: disable = no-name-in-module # pylint: disable = import-error
)
from google.api_core.gapic_v1.client_info import ClientInfo
from google.cloud import (
    documentai,  # type: ignore # pylint: disable = no-name-in-module # pylint: disable = import-error
)

USER_AGENT = "cloud-solutions/eks-docai-v1"


def batch_classify_documents(
    project_id: str,
    location: str,
    processor_id: str,
    gcs_input_prefix: str,
    gcs_output_uri: str,
    processor_version_id: Optional[str] = None,
    field_mask: Optional[str] = None,
    timeout: int = 400,
):
    """Function for processing PDF documents in batch"""
    # You must set the `api_endpoint` if you use a location other than "us".
    opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")

    client = documentai.DocumentProcessorServiceClient(
        client_options=opts, client_info=ClientInfo(user_agent=USER_AGENT)
    )

    # Specify a GCS URI Prefix to process an entire directory
    gcs_prefix = documentai.GcsPrefix(gcs_uri_prefix=gcs_input_prefix)
    input_config = documentai.BatchDocumentsInputConfig(gcs_prefix=gcs_prefix)

    # Cloud Storage URI for the Output Directory
    gcs_output_config = documentai.DocumentOutputConfig.GcsOutputConfig(
        gcs_uri=gcs_output_uri, field_mask=field_mask
    )

    # Where to write results
    output_config = documentai.DocumentOutputConfig(gcs_output_config=gcs_output_config)

    if processor_version_id:
        # The full resource name of the processor version, e.g.:
        # projects/{project_id}/locations/{location}/processors/
        # {processor_id}/processorVersions/{processor_version_id}
        name = client.processor_version_path(
            project_id, location, processor_id, processor_version_id
        )
    else:
        # The full resource name of the processor, e.g.:
        # projects/{project_id}/locations/{location}/processors/{processor_id}
        name = client.processor_path(project_id, location, processor_id)

    request = documentai.BatchProcessRequest(
        name=name,
        input_documents=input_config,
        document_output_config=output_config,
    )

    # BatchProcess returns a Long Running Operation (LRO)
    operation = client.batch_process_documents(request)
    logging.info(f"Started batch process; {operation.metadata=};")

    # Continually polls the operation until it is complete.
    # This could take some time for larger files
    # Format: projects/{project_id}/locations/{location}/operations/{operation_id}
    try:
        logging.info(
            f"Waiting for operation {operation.operation.name} to " f"complete..."
        )
        operation.result(timeout=timeout)
    # Catch exception when operation doesn't finish before timeout
    except (RetryError, InternalServerError) as e:
        logging.error(e.message)

    # NOTE: Can also use callbacks for asynchronous processing
    #
    # def my_callback(future):
    #   result = future.result()
    #
    # operation.add_done_callback(my_callback)


# Main entry point
if __name__ == "__main__":
    # Retrieve Job-defined env vars
    TASK_INDEX = os.getenv("CLOUD_RUN_TASK_INDEX", 0)
    TASK_ATTEMPT = os.getenv("CLOUD_RUN_TASK_ATTEMPT", 0)

    # Retrieve User-defined env vars
    PROJECT_ID = os.getenv("PROJECT_ID")
    LOCATION = os.getenv("LOCATION")
    PROCESSOR_ID = os.getenv("PROCESSOR_ID")
    GCS_INPUT_PREFIX = os.getenv("GCS_INPUT_PREFIX")
    GCS_OUTPUT_URI = os.getenv("GCS_OUTPUT_URI")

    if (
        not PROJECT_ID
        or not LOCATION
        or not PROCESSOR_ID
        or not GCS_INPUT_PREFIX
        or not GCS_OUTPUT_URI
    ):
        message = (
            f"Environment variables missing; "
            f"{PROJECT_ID=}, "
            f"{LOCATION=}, "
            f"{PROCESSOR_ID=}, "
            f"{GCS_INPUT_PREFIX=}, "
            f"{GCS_OUTPUT_URI=}"
        )
        logging.error(message)
        sys.exit(1)

    try:
        logging.info(f"Starting Task #{TASK_INDEX} (att. {TASK_ATTEMPT}.")
        logging.info(
            f"{PROCESSOR_ID=}, "
            f"{PROJECT_ID=}, "
            f"{LOCATION=}, "
            f"{GCS_INPUT_PREFIX=}, "
            f"{GCS_OUTPUT_URI=}"
        )
        batch_classify_documents(
            project_id=PROJECT_ID,
            location=LOCATION,
            processor_id=PROCESSOR_ID,
            gcs_input_prefix=GCS_INPUT_PREFIX,
            gcs_output_uri=GCS_OUTPUT_URI,
        )
        logging.info(f"Completed Task #{TASK_INDEX} (att. {TASK_ATTEMPT}.")
    except Exception as e:
        logging.error(f"Task Index {TASK_INDEX} (att. {TASK_ATTEMPT} failed!" f"{e}")
        sys.exit(1)
