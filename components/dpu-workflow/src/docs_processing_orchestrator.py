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

import os
import sys
import logging
from datetime import datetime, timedelta

from airflow import DAG  # type: ignore
from airflow.models.param import Param  # type: ignore
from airflow.operators.dummy import DummyOperator  # type: ignore
from airflow.operators.python import (
    BranchPythonOperator,  # type: ignore
    PythonOperator,
)
from airflow.providers.google.cloud.operators.bigquery import \
    BigQueryCreateEmptyTableOperator  # type: ignore
from airflow.providers.google.cloud.operators.cloud_run import \
    CloudRunExecuteJobOperator  # type: ignore
from airflow.providers.google.cloud.operators.gcs import \
    GCSListObjectsOperator  # type: ignore
from airflow.providers.google.cloud.transfers.gcs_to_gcs import \
    GCSToGCSOperator  # type: ignore
from airflow.utils.trigger_rule import TriggerRule  # type: ignore
from google.api_core.gapic_v1.client_info import ClientInfo  # type: ignore
from airflow.exceptions import AirflowSkipException

from utils import file_utils, datastore_utils, cloud_run_utils


sys.path.insert(0,os.path.abspath(os.path.dirname(__file__)))

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 5, 12),  # Adjust as needed
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 0,
}

# This is the list of expected potential labels coming back from the classifier
# any label that is not in this list, would be treated as a "general" pdf and
# would be processed accordingly.
# Also note, that labels will be matched case-insensitive and disregarding
# trailing and leading whitespaces.
KNOWN_LABELS_FOR_CLASSIFIER = [
    "form"
]


def get_supported_file_types(**context):
    file_list = context["ti"].xcom_pull(task_ids="list_all_input_files")
    file_type_to_processor = context["params"]["supported_files"]
    files_by_type = file_utils.supported_files_by_type(file_list,
                                                       file_type_to_processor)
    context["ti"].xcom_push(key="types_to_process", value=files_by_type)

def has_files_to_process(**context):
    files_to_process = context["ti"].xcom_pull(key="types_to_process")
    if files_to_process:
        return "create_process_folder"
    else:
        return "skip_bucket_creation"

def generate_process_folder(**context):
    process_folder = file_utils.get_random_process_folder_name()
    context["ti"].xcom_push(key="process_folder", value=process_folder)

def generate_mv_params(**context):
    files_to_process = context["ti"].xcom_pull(key="types_to_process")
    process_folder = context["ti"].xcom_pull(key="process_folder")
    input_folder = context["params"]["input_folder"]
    process_bucket = os.environ.get("DPU_PROCESS_BUCKET")

    parameter_obj_list = file_utils.get_mv_params(files_to_process,
                                                  input_folder,
                                       process_bucket, process_folder)
    return parameter_obj_list

def generate_classify_job_params_fn(**context):
    classifier_params = context["params"]["classifier"]
    if (not classifier_params.get("project_id") or
        not classifier_params.get("location") or
        not classifier_params.get("processor_id")):
        logging.warning(f"Not all required parameters for the classifier are "
                        f"provided (required `project_id`, `location` and "
                        f"`processor_id`). {classifier_params=}")
        raise AirflowSkipException()
    process_folder = context["ti"].xcom_pull(key="process_folder")
    process_bucket = os.environ.get("DPU_PROCESS_BUCKET")
    assert process_bucket is not None, "DPU_PROCESS_BUCKET is not set"

    return cloud_run_utils.get_doc_classifier_job_overrides(
        classifier_project_id=classifier_params["project_id"],
        classifier_location=classifier_params["location"],
        classifier_processor_id=classifier_params["processor_id"],
        process_folder=process_folder,
        process_bucket=process_bucket,
    )

def parse_doc_classifier_output(**context):
    process_bucket = os.environ.get("DPU_PROCESS_BUCKET")
    assert process_bucket is not None, "DPU_PROCESS_BUCKET is not set"
    process_folder = context["ti"].xcom_pull(key="process_folder")
    parsed_output = cloud_run_utils.read_classifier_job_output(
        process_bucket, process_folder, KNOWN_LABELS_FOR_CLASSIFIER)
    # context["ti"].xcom_push(key="classifier_output", value=parsed_output)
    return parsed_output

def data_store_import_docs(**context):
    data_store_region = os.environ.get("DPU_DATA_STORE_REGION")
    bq_table = context["ti"].xcom_pull(key="bigquery_table")

    operation_name = datastore_utils.import_docs_to_datastore(
        bq_table,
        data_store_region,
        os.environ.get("DPU_DATA_STORE_ID")
    )
    return operation_name

def generate_process_job_params(**context):
    mv_params = context["ti"].xcom_pull(
        key="return_value", task_ids="generate_files_move_parameters"
    )
    if not mv_params:
        logging.warning("No need to run, since generate_files_move_parameters "
                        "did not generate any files to process")
        raise AirflowSkipException()
    bq_table = context["ti"].xcom_pull(key="bigquery_table")
    doc_processor_job_name = os.environ.get("DOC_PROCESSOR_JOB_NAME")
    gcs_reject_bucket = os.environ.get("DPU_REJECT_BUCKET")

    process_job_params = cloud_run_utils.get_process_job_params(bq_table,
                                                doc_processor_job_name,
                                                gcs_reject_bucket, mv_params)
    return process_job_params

def generate_output_table_name(**context):
    process_folder = context["ti"].xcom_pull(key="process_folder")
    output_table_name = process_folder.replace("-", "_")
    context["ti"].xcom_push(key="output_table_name", value=output_table_name)

def generate_form_process_job_params(**context):
    # Build BigQuery table id <project_id>.<dataset_id>.<table_id>
    bq_table = context["ti"].xcom_pull(key="bigquery_table")

    # Build GCS input and out prefix - gs://<process_bucket_name>/<process_folder>/pdf_forms/<input|output>
    process_bucket = os.environ.get("DPU_PROCESS_BUCKET")
    process_folder = context["ti"].xcom_pull(key="process_folder")

    form_parser_job_params = cloud_run_utils.forms_parser_job_params(
        bq_table,
        process_bucket,
        process_folder,
    )
    return form_parser_job_params

def generate_pdf_forms_folder(**context):
    process_folder = context["ti"].xcom_pull(key="process_folder")
    pdf_forms_folder = f"{process_folder}/pdf-form/input/"
    context["ti"].xcom_push(key="pdf_forms_folder", value=pdf_forms_folder)


with DAG(
    "run_docs_processing",
    default_args=default_args,
    schedule_interval=None,
    params={
        "input_bucket": os.environ.get("DPU_INPUT_BUCKET"),
        "process_bucket": os.environ.get("DPU_PROCESS_BUCKET"),
        "input_folder": "",
        "supported_files": Param(
            [
                {"file-suffix": "pdf", "processor": "agent-builder"},
                {"file-suffix": "txt", "processor": "agent-builder"},
                {"file-suffix": "html", "processor": "agent-builder"},
                {"file-suffix": "msg", "processor": "dpu-doc-processor"},
                {"file-suffix": "zip", "processor": "dpu-doc-processor"},
                {"file-suffix": "xlsx", "processor": "dpu-doc-processor"},
                {"file-suffix": "xlsm", "processor": "dpu-doc-processor"},
            ],
            type="array",
            items={
                "type": "object",
                "properties": {
                    "file-suffix": {"type": "string"},
                    "processor": {"type": "string"},
                },
                "required": ["file-suffix", "processor"],
            },
        ),
        "classifier": Param(
            default={
                "project_id":   "",
                "location":     "",
                "processor_id": "",
            },
            type="object",
            properties={
                "project_id":   {"type": "string"},
                "location":     {"type": "string"},
                "processor_id": {"type": "string"},
            },
            required=["project_id", "location", "processor_id"],
        ),
    },
) as dag:
    GCS_Files = GCSListObjectsOperator(
        task_id="list_all_input_files",
        prefix="{{ params.input_folder if params.input_folder }}",
        bucket="{{ params.input_bucket }}",
    )

    process_supported_types = PythonOperator(
        task_id="process_supported_types",
        python_callable=get_supported_file_types,
        params={
            "supported_files": Param(
                "{{ params.supported_files }}",
                type="array",
                items={
                    "type": "object",
                    "properties": {
                        "file-suffix": {"type": "string"},
                        "processor": {"type": "string"},
                    },
                    "required": ["file-suffix", "processor"],
                },
            )
        },
        provide_context=True,
    )

    has_files = BranchPythonOperator(
        task_id="has_files_to_process",
        python_callable=has_files_to_process,
        provide_context=True,
    )

    create_process_folder = PythonOperator(
        task_id="create_process_folder",
        python_callable=generate_process_folder,
        provide_context=True,
    )

    skip_bucket_creation = PythonOperator(
        task_id="skip_bucket_creation",
        python_callable=lambda: print(
            "No supported file type found, processing ends here!"
        ),
    )

    generate_files_move_parameters = PythonOperator(
        task_id="generate_files_move_parameters",
        python_callable=generate_mv_params,
        provide_context=True,
    )

    move_to_processing = GCSToGCSOperator.partial(
        task_id="move_file",
        source_bucket="{{ params.input_bucket }}",
        move_object=True,
    ).expand_kwargs(generate_files_move_parameters.output)

    generate_classify_job_params = PythonOperator(
        task_id="generate_classify_job_params",
        python_callable=generate_classify_job_params_fn,
        provide_context=True,
    )

    execute_doc_classifier = CloudRunExecuteJobOperator.partial(
        project_id=os.environ.get("GCP_PROJECT"),
        region=os.environ.get("DPU_REGION"),
        task_id="execute_doc_classifier",
        job_name=os.environ.get("DOC_CLASSIFIER_JOB_NAME"),
        deferrable=False,
    ).expand_kwargs([generate_classify_job_params.output])

    parse_doc_classifier_results_and_move_files = PythonOperator(
        task_id="parse_doc_classifier_results_and_move_files",
        python_callable=parse_doc_classifier_output,
        provide_context=True,
    )

    classified_docs_moved_or_skipped = DummyOperator(
        task_id='classified_docs_moved_or_skipped',
        trigger_rule=TriggerRule.ALL_DONE
    )

    create_output_table_name = PythonOperator(
        task_id="create_output_table_name",
        python_callable=generate_output_table_name,
        provide_context=True,
    )

    create_output_table = create_bigquery_table = BigQueryCreateEmptyTableOperator(
        task_id="create_output_table",
        dataset_id=os.environ.get("DPU_OUTPUT_DATASET"),  # pyright: ignore[reportArgumentType]
        table_id="{{ ti.xcom_pull(task_ids='create_output_table_name', key='output_table_name') }}",
        schema_fields=[
            {"name": "id", "mode": "REQUIRED", "type": "STRING", "fields": []},
            {"name": "jsonData", "mode": "NULLABLE", "type": "STRING", "fields": []},
            {
                "name": "content",
                "type": "RECORD",
                "mode": "NULLABLE",
                "fields": [
                    {"name": "mimeType", "type": "STRING", "mode": "NULLABLE"},
                    {"name": "uri", "type": "STRING", "mode": "NULLABLE"},
                ],
            },
        ],
    )

    create_process_job_params = PythonOperator(
        task_id="create_process_job_params",
        python_callable=generate_process_job_params,
        provide_context=True,
    )

    execute_doc_processors = CloudRunExecuteJobOperator.partial(
        project_id=os.environ.get("GCP_PROJECT"),
        region=os.environ.get("DPU_REGION"),
        task_id="execute_doc_processors",
        job_name=os.environ.get("DOC_PROCESSOR_JOB_NAME"),
        deferrable=False,
    ).expand_kwargs(create_process_job_params.output)

    import_docs_to_data_store = PythonOperator(
        task_id="import_docs_to_data_store",
        python_callable=data_store_import_docs,
        execution_timeout=timedelta(seconds=3600),
        provide_context=True,
    )

    import_forms_to_data_store = PythonOperator(
        task_id="import_forms_to_data_store",
        python_callable=data_store_import_docs,
        execution_timeout=timedelta(seconds=3600),
        provide_context=True,
    )

    create_form_process_job_params = PythonOperator(
        task_id="create_form_process_job_params",
        python_callable=generate_form_process_job_params,
        provide_context=True,
    )

    execute_forms_parser = CloudRunExecuteJobOperator.partial(
        # Calling os.environ[] instead of using the .get method to verify we
        # have set environment variables, not allowing None values.
        project_id=os.environ["GCP_PROJECT"],
        region=os.environ["DPU_REGION"],
        task_id="execute_forms_parser",
        job_name=os.environ["FORMS_PARSER_JOB_NAME"],
        deferrable=False,
    ).expand_kwargs(
        # Converting to a list, since expand_kwargs expects a list,
        # even though we have only one task to execute.
        [create_form_process_job_params.output]
    )

    (
        # initial common actions - ends with a decision whether to continue
        # to basic processing, or stop working
        GCS_Files
        >> process_supported_types
        >> has_files
        >> [create_process_folder, skip_bucket_creation]
    )   # pyright: ignore[reportOperatorIssue]
    (
        # In the case we continue working, moving documents to processing
        # folder, and creating an output table where metadata will be saved
            create_process_folder
            >> create_output_table_name
            >> create_output_table
            >> generate_files_move_parameters
            >> move_to_processing

            # We then want to see if there are any forms, since those will be
            # handled differently.
            >> generate_classify_job_params
            >> execute_doc_classifier
            >> parse_doc_classifier_results_and_move_files
            >> classified_docs_moved_or_skipped
    )

    (
        # Continue to process forms, depending on move_forms executed
        # successfully. This doesn't have to wait for general processing.
            parse_doc_classifier_results_and_move_files
            >> create_form_process_job_params
            >> execute_forms_parser
            >> import_forms_to_data_store

    )

    (
        # General document processing has to wait for the forms to
        # move/skipped, since we don't want to process the forms using this job.
        classified_docs_moved_or_skipped
        >> create_process_job_params
        >> execute_doc_processors
        >> import_docs_to_data_store
     )


