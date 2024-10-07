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

import argparse
import logging
import sys
from dataclasses import dataclass

from google.api_core.gapic_v1.client_info import ClientInfo
from google.cloud import storage, bigquery

import alloydb
import bigquery
import docai
import gcs

USER_AGENT = "cloud-solutions/eks-docai-v1"


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        "--run-id",
        dest="run_id",
        help="The run ID from Composer to help identify documents.",
        required=True,
    )
    parser.add_argument(
        "--processor-project",
        dest="processor_project",
        help="The project ID where the DocAI processor is created.",
        required=True,
    )
    parser.add_argument(
        "--processor-location",
        dest="processor_location",
        help="The location where the DocAI processor is created.",
        required=True,
    )
    parser.add_argument(
        "--processor-id",
        dest="processor_id",
        help="The processor ID.",
        required=True,
    )
    parser.add_argument(
        "--gcs-input-prefix",
        dest="gcs_input_prefix",
        help="GCS prefix with the input documents",
        required=True,
    )
    parser.add_argument(
        "--gcs-output-uri",
        dest="gcs_output_uri",
        help="GCS uri to write the processor results to",
        required=True,
    )
    parser.add_argument(
        "--alloydb-project",
        dest="alloydb_project",
        help="AlloyDB Project",
        required=True,
    )
    parser.add_argument(
        "--alloydb-project",
        dest="alloydb_project",
        help="AlloyDB Project",
        required=True,
    )
    parser.add_argument(
        "--alloydb-location",
        dest="alloydb_project",
        help="AlloyDB Project",
        required=True,
    )
    parser.add_argument(
        "--bigquery-dataset",
        dest="bigquery_dataset",
        help="BigQuery Dataset",
        required=True,
    )
    parser.add_argument(
        "--bigquery-dataset",
        dest="bigquery_dataset",
        help="BigQuery Dataset",
        required=True,
    )
    parser.add_argument(
        "--bigquery-table",
        dest="bigquery_table",
        help="BigQuery Table",
        required=True,
    )
    return parser


@dataclass
class DetectedEntity:
    original_filename: str
    entity_type: str
    raw_text: str
    normalized_text: str
    confidence: float
    run_id: str
    results_file: str



def run() -> None:
    parser = create_parser()
    args = parser.parse_args(sys.argv[1:])
    alloydb_connection = alloydb.create_alloydb_connection_pool(
        args.alloydb_project,
        args.alloydb_location,
        args.alloydb_cluster,
        args.alloydb_instance,
        args.alloydb_database
    )
    storage_client = storage.Client(client_info=ClientInfo(user_agent=USER_AGENT))
    logging.info("Verifying AlloyDB output table")
    alloydb.verify_alloydb_table(alloydb_connection)
    logging.info("Starting Batch Processor operation")
    batch_operation = docai.call_batch_processor(
        args.project_id,
        args.location,
        args.processor_id,
        args.gcs_input_prefix,
        args.gcs_output_uri
    )
    logging.info("Waiting for Batch operation to finish")
    individual_process_statuses = docai.wait_for_completion_and_verify_success(batch_operation)
    logging.info(f"Parsing results from {args.gcs_output_uri}")
    parsed_results = docai.read_and_parse_batch_results(
        storage_client, 
        individual_process_statuses, 
        args.gcs_input_prefix,
        args.run_id,
    )
    bucket_name, csv_blob_name = gcs.write_results_to_gcs(storage_client, parsed_results, args.gcs_output_uri)
    alloydb.write_results_to_alloydb(bucket_name, csv_blob_name, alloydb_connection)
    bigquery.write_results_to_bigquery(bucket_name, csv_blob_name, args.bigquery_project, args.bigquery_dataset, args.bigquery_table)


if __name__ == "__main__":
    run()
