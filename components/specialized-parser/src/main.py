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
import re
from typing import Optional, Tuple

from configs import JobConfig, ProcessorConfig, AlloyDBConfig, BigQueryConfig
from runner import SpecializedParserJobRunner


def is_valid_processor_id(processor_id: str) -> Optional[Tuple[str, str, str]]:
  """
  Validates a GCP DocumentAI processor ID.

  Args:
    processor_id: The processor ID string to validate.

  Returns:
    Tuple (project_id, location, processor_id) if the processor ID is valid, False otherwise.
  """
  pattern = r"^projects\/([a-z][a-z0-9\-]{4,28}[a-z0-9])\/locations\/(us|eu)\/processors\/([a-zA-Z0-9_-]+)$"
  match = re.match(pattern, processor_id)
  if not match:
      return None
  return match.group(1), match.group(2), match.group(3)


def run() -> None:
    # required params via environment variables
    print("Reading environment variables for configuration")
    print(f"{os.environ=}")
    processor_id = os.getenv("PROCESSOR_ID")
    gcs_input_prefix = os.getenv("GCS_INPUT_PREFIX")
    gcs_output_uri = os.getenv("GCS_OUTPUT_URI")
    bigquery_metadata_table = os.getenv("BQ_TABLE")
    
    valid_processor_tuple = is_valid_processor_id(processor_id)
    if not valid_processor_tuple:
        raise ValueError(f"processor_id is missing or invalid. {processor_id=}")
    
    job_config = JobConfig(
        run_id=os.getenv("RUN_ID", "no-run-id-specified"),
        gcs_input_prefix=gcs_input_prefix,
        gcs_output_uri=gcs_output_uri,
    )
    
    processor_config = ProcessorConfig(
        project=valid_processor_tuple[0],
        location=valid_processor_tuple[1],
        processor_id=valid_processor_tuple[2],
        timeout=int(os.getenv("PROCESSOR_TIMEOUT", "600")),
    )
    bigquery_config = BigQueryConfig(
        general_output_table_id=bigquery_metadata_table,
    )
    alloydb_config = AlloyDBConfig(
        # alloydb primary instance is set by terraform, and already in the form of:
        # "projects/<PROJECT>/locations/<LOCATION>/clusters/<CLUSTER>/instances/<INSTANCE>"
        # If you override the environment variable, make sure to use the same format.
        primary_instance=os.getenv("ALLOYDB_INSTANCE"),
        database=os.getenv("ALLOYDB_DATABASE"),
    )
    runner = SpecializedParserJobRunner(
        job_config=job_config,
        alloydb_config=alloydb_config,
        processor_config=processor_config,
        bigquery_config=bigquery_config,
    )
    runner.run()

if __name__ == "__main__":
    run()
