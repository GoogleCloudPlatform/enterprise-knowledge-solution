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


# pylint: disable=import-error


#
# Import libraries
#

import site
import os

site.addsitedir(os.path.join(os.path.dirname(__file__), "libs"))


#
# Normal functionality
#

from processors.base.gcsio import GCSPath  # noqa E402
from processors.base.result_writer import get_bq_writer  # noqa E402
from processors.msg.main_processor import process_object  # noqa E402

from cloudevents.http import CloudEvent  # noqa E402
import functions_framework  # noqa E402
import os  # noqa E402
import logging  # noqa E402


# Setup logging
logging.basicConfig(format="%(asctime)s %(name)s: %(message)s")
logging.getLogger("processors").setLevel(
    logging.DEBUG if os.getenv("DEBUG", "TRUE") else logging.INFO
)


# Triggered by a change in a storage bucket
@functions_framework.cloud_event
def process_gcs(cloud_event: CloudEvent) -> None:
    """This function is triggered by a change in a storage bucket.

    Args:
        cloud_event: The CloudEvent that triggered this function.
    Returns:
        The event ID, event type, bucket, name,
        metageneration, and timeCreated.
    """

    # Validate this is an object to process
    prefix = os.getenv("GCS_PREFIX", "")
    if not cloud_event.data["name"].startswith(prefix):
        return

    # Construct the GCS Path object
    obj = GCSPath(
        f'gs://{cloud_event.data["bucket"]}/{cloud_event.data["name"]}',
        crc32c=cloud_event.data["crc32c"],
    )

    # Find destination obj
    dest_obj = GCSPath(
        os.getenv("PROCESS_BUCKET"), cloud_event.data["name"].removeprefix(prefix)
    )

    # Move it across
    obj.move(dest_obj)

    # Construct parameters
    with_html = os.getenv("WITH_HTML", "TRUE") == "TRUE"
    write_json = os.getenv("WRITE_JSON", "TRUE") == "TRUE"
    bq_writer = get_bq_writer(os.getenv("BQ_RESULTS_TABLE", ""))

    # Process object
    print(f"Doc Processor processing {str(dest_obj)}")
    process_object(
        dest_obj, with_html=with_html, write_json=write_json, bq_writer=bq_writer
    )
