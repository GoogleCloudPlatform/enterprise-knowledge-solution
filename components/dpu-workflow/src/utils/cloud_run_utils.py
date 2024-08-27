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



def forms_parser_job_params(bq_table, process_bucket, process_folder):
    bq_table_id = f"{bq_table['project_id']}.{bq_table['dataset_id']}.{bq_table['table_id']}"
    gcs_input_prefix = f"gs://{process_bucket}/{process_folder}/pdf-forms/input/"
    gcs_output_prefix = f"gs://{process_bucket}/{process_folder}/pdf-forms/output/"

    return {
        "overrides": {
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
    }