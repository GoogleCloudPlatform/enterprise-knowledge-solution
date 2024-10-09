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

import csv
import logging
import re
from dataclasses import asdict
from typing import List, Tuple

from google.cloud import storage
from main import DetectedEntity


def write_results_to_gcs(
    storage_client: storage.Client,
    parsed_results: List[DetectedEntity],
    gcs_output_uri: str,
) -> Tuple[str, str]:
    """
    Write the detected entities to the GCS bucket as a CSV
    Args:
        storage_client: the storage client
        parsed_results: a list of results to write in the CSV
        gcs_output_uri: where to write the results - this should point to a folder, as a hard-coded filename will be appended

    Returns:
        A tuple, representing the bucket name and the full path to the CSV inside the bucket.
    """
    bucket_name, output_folder = get_bucket_name(gcs_output_uri)
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(output_folder + "/invoice_parser_results.csv")
    data_dicts = [asdict(d) for d in parsed_results]
    with blob.open("w") as f:
        # not sure why pyright detects `f` as an invalid argument type for csv.DictWriter as an error - this actually works
        writer = csv.DictWriter(
            f, fieldnames=data_dicts[0].keys()
        )  # pyright: ignore [reportArgumentType]
        writer.writeheader()
        writer.writerows(data_dicts)
    return bucket_name, str(blob.name)


def get_bucket_name(gcs_output_uri: str) -> Tuple[str, str]:
    """
    Function to get a GCS uri, in the format of `gs://<BUCKET>/<PATH>` and return a tuple of the bucket name and the output path.
    Args:
        gcs_output_uri: The prefix GCS path in the format of `gs://<BUCKET>/<PATH>`

    Returns: A tuple, with the first field being the bucket name and the second the path in the bucket

    """
    match = re.search(r"gs://([^/]+)/(.*)", gcs_output_uri)

    if match:
        bucket_name = match.group(1)
        output_folder = match.group(2)
        logging.info(f"{bucket_name=}; {output_folder=}")
        return bucket_name, output_folder
    else:
        logging.error("No bucket name found in the given string.")
        raise ValueError(f"Could not extract bucket from {gcs_output_uri}")
