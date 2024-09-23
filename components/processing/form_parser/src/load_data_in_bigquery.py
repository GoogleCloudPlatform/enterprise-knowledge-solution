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

import json
import logging
import re
import uuid

from google.cloud import bigquery, documentai


def load_rows_into_bigquery(rows_to_insert, table_id):
    """Program that loads list of rows in BigQuery.

    Args:
        rows_to_insert: list of rows with each row as json string,
        table_id: bigquery table id
    """
    # Construct a BigQuery client object.
    client = bigquery.Client()
    # Make an API request to insert rows into the table
    errors = client.insert_rows_json(table_id, rows_to_insert)

    if errors == []:
        print(
            "New rows have been added in Big Query table."
        )  # @todo remove all print statements
        logging.info("New rows have been added in Big Query table.")
    else:
        print("Encountered errors while inserting rows in BigQuery: {}".format(errors))
        logging.error(
            "Encountered errors while inserting rows in BigQuery: {}".format(errors)
        )


def build_bq_metadata_row(original_file_path, text_file_path):
    """Program that builds metadata for each processed file

    Args:
        original_file_path: original pdf file path in GCS,
        text_file_path: txt file path in GCS
    """
    # generate unique id
    id = str(uuid.uuid4())
    print(f"id: {id}")

    # build row with metadata
    row = {
        "id": id,
        "jsonData": json.dumps(
            {
                "objs": [
                    {
                        "uri": text_file_path,
                        "objid": id,
                        "status": "Indexed",
                        "mimetype": "text/plain",
                    },
                    {
                        "uri": original_file_path,
                        "objid": "",
                        "status": "",
                        "mimetype": "application/pdf",
                    },
                ]
            }
        ),
        "content": {"mimeType": "text/plain", "uri": text_file_path},
    }
    return row


def build_output_metadata(blob, storage_client, gcs_input_prefix, gcs_output_uri):
    """Program that downloads JSON File as bytes object and converts to Document Object

    Args:
        blob: output object (processed by form parser),
        storage_client: Cloud Storage client,
        gcs_input_prefix: GCS bucket prefix for PDF with forms
        gcs_output_uri: GCS bucket prefix that is used to store processed objects
    """

    # Download JSON File as bytes object and convert to Document Object
    logging.info(f"Fetching {blob.name}")
    document = documentai.Document.from_json(
        blob.download_as_bytes(), ignore_unknown_fields=True
    )

    # Read the text recognition output from the processor @TODO update log level to debug
    print("The document contains the following text:")
    print(document.text)

    # Create a .txt file from .json file
    bucket_name = get_bucket_name(gcs_output_uri)
    txt_filename = blob.name.replace(".json", ".txt")
    bucket = storage_client.bucket(bucket_name)
    new_blob = bucket.blob(txt_filename)
    new_blob.upload_from_string(document.text)
    txt_file_path = f"gs://{bucket_name}/{txt_filename}"
    print(f"Text file {txt_file_path} created successfully")
    logging.info(f"Text file {txt_file_path} created successfully")

    # Get original file name from output file name
    # Remove .json ext with the number after last occurance of - and number. Then remove output gcs output prefix
    original_filename = (blob.name.rsplit("-", 1)[0]).rsplit("/", 1)[1]
    original_file_path = f"{gcs_input_prefix}{original_filename}.pdf"
    print(f"original filename: {original_file_path}")
    logging.info(f"original filename: {original_file_path}")

    return build_bq_metadata_row(original_file_path, txt_file_path)


def get_bucket_name(gcs_output_uri):
    """Program that fetches the GCS bucket name where processed objects are stored

    Args:
        gcs_output_uri: GCS bucket prefix that is used to store processed objects
    """
    # Use regular expression to match the bucket name
    match = re.search(r"gs://([^/]+)/", gcs_output_uri)

    if match:
        bucket_name = match.group(1)
        print(f"Bucket name: {bucket_name}")
        logging.info(f"Bucket name: {bucket_name}")
        return bucket_name
    else:
        print("No bucket name found in the given string.")
        logging.info("No bucket name found in the given string.")
