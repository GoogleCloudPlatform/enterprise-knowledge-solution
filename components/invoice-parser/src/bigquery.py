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


from google.cloud import bigquery


def write_results_to_bigquery(
    bucket_name: str,
    csv_blob_name: str,
    bigquery_project: str,
    bigquery_dataset: str,
    bigquery_table: str,
):
    """Loads data from a CSV file in GCS to a BigQuery table with append logic.

    Args:
      bucket_name: The name of the GCS bucket.
      csv_blob_name: The name of the blob (file) in GCS.
      bigquery_project: The ID of the BigQuery project.
      bigquery_dataset: The ID of the BigQuery dataset.
      bigquery_table: The ID of the BigQuery table.
    """
    # Construct a BigQuery client object.
    client = bigquery.Client()

    # Construct the full table ID.
    table_ref = client.get_dataset(f"{bigquery_project}.{bigquery_dataset}").table(
        bigquery_table
    )

    # Configure the load job.
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",  # Append data to the table
        source_format=bigquery.SourceFormat.CSV,
        autodetect=True,  # Automatically detect schema
    )

    # Construct the URI for the CSV file in GCS.
    uri = f"gs://{bucket_name}/{csv_blob_name}"

    # Create and run the load job.
    load_job = client.load_table_from_uri(uri, table_ref, job_config=job_config)
    load_job.result()  # Wait for the job to complete
