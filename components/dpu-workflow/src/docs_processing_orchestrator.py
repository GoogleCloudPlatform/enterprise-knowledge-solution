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

import logging
import os
import sys
from datetime import datetime, timedelta

from airflow import DAG  # type: ignore
from airflow.exceptions import AirflowSkipException
from airflow.models.param import Param  # type: ignore
from airflow.operators.dummy import DummyOperator  # type: ignore
from airflow.operators.python import BranchPythonOperator  # type: ignore
from airflow.operators.python import PythonOperator, ShortCircuitOperator
from airflow.providers.google.cloud.operators.bigquery import (  # type: ignore
    BigQueryCreateEmptyTableOperator,
)
from airflow.providers.google.cloud.operators.cloud_run import (  # type: ignore
    CloudRunExecuteJobOperator,
)
from airflow.providers.google.cloud.operators.gcs import (  # type: ignore
    GCSListObjectsOperator,
)
from airflow.providers.google.cloud.transfers.gcs_to_gcs import (  # type: ignore
    GCSToGCSOperator,
)
from airflow.utils.task_group import TaskGroup
from airflow.utils.trigger_rule import TriggerRule  # type: ignore
from utils import cloud_run_utils, datastore_utils, file_utils, gcs_utils

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 5, 12),  # Adjust as needed
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 0,
}

USER_AGENT = "cloud-solutions/eks-orchestrator-v1"
# This is the list of expected potential labels coming back from the classifier
# any label that is not in this list, would be treated as a "general" pdf and
# would be processed accordingly.
# Also note, that labels will be matched case-insensitive and disregarding
# trailing and leading whitespaces.
KNOWN_LABELS_FOR_CLASSIFIER = ["form"]


def get_supported_file_types(**context):
    file_type_to_processor = context["params"]["supported_files"]
    files_list = context["ti"].xcom_pull(
        task_ids="initial_load_from_input_bucket.list_all_input_files"
    )

    files_by_type, unsupported_files = file_utils.supported_files_by_type(
        files_list, file_type_to_processor
    )
    context["ti"].xcom_push(key="types_to_process", value=files_by_type)
    context["ti"].xcom_push(key="files_to_reject", value=unsupported_files)


def has_files_to_process(**context):
    files_to_process = context["ti"].xcom_pull(
        task_ids="initial_load_from_input_bucket.process_supported_types",
        key="types_to_process",
    )
    if files_to_process:
        return "initial_load_from_input_bucket.create_process_folder"
    else:
        return "initial_load_from_input_bucket.skip_bucket_creation"


def generate_process_folder(**context):
    process_folder = file_utils.get_random_process_folder_name()
    context["ti"].xcom_push(key="process_folder", value=process_folder)


def generate_check_duplicated_files_job_params_fn(**context):
    input_bucket = context["params"]["input_bucket"]
    input_folder = context["params"]["input_folder"]
    input_folder_ful_uri = input_bucket if not input_folder else f"{input_bucket}/{input_folder}"
    process_folder = context["ti"].xcom_pull(
        task_ids="initial_load_from_input_bucket.create_process_folder",
        key="process_folder",
    )
    output_folder = f'{os.environ.get("DPU_PROCESS_BUCKET")}/{process_folder}/workflow-io/check_duplicated_files'
    context["ti"].xcom_push(key="output_folder", value=output_folder)
    return cloud_run_utils.get_doc_registry_duplicate_job_override(input_folder_ful_uri, output_folder)


def move_duplicated_files_to_rejected_bucket_fn(**context):
    output_folder = context["ti"].xcom_pull(
        task_ids="initial_load_from_input_bucket.generate_check_duplicated_files_job_params",
        key="output_folder",
    )
    process_folder = context["ti"].xcom_pull(
        task_ids="initial_load_from_input_bucket.create_process_folder",
        key="process_folder",
    )
    process_files_by_type = context["ti"].xcom_pull(
        task_ids="initial_load_from_input_bucket.process_supported_types",
        key="types_to_process",
    )
    gcs_utils.move_duplicated_files(f'{output_folder}/result.jsonl', f'{os.environ.get("DPU_REJECT_BUCKET")}/{process_folder}', process_files_by_type)
    for key in list(process_files_by_type):
        if not process_files_by_type[key]:
            del process_files_by_type[key]
    return process_files_by_type


def has_files_to_process_after_removing_duplicates_fn(**context):
    files_to_process = context["ti"].xcom_pull(
        key="return_value",
        task_ids="initial_load_from_input_bucket.move_duplicated_files_to_rejected_bucket"
    )
    if files_to_process:
        return "initial_load_from_input_bucket.generate_files_move_parameters"
    else:
        return "initial_load_from_input_bucket.skip_move_files"


def generate_mv_params(**context):
    files_to_process = context["ti"].xcom_pull(
        key="return_value",
        task_ids="initial_load_from_input_bucket.move_duplicated_files_to_rejected_bucket"
    )
    process_folder = context["ti"].xcom_pull(
        task_ids="initial_load_from_input_bucket.create_process_folder",
        key="process_folder",
    )
    input_folder = context["params"]["input_folder"]
    process_bucket = os.environ.get("DPU_PROCESS_BUCKET")

    parameter_obj_list = file_utils.get_mv_params(
        files_to_process, input_folder, process_bucket, process_folder
    )
    return parameter_obj_list


def generate_classify_job_params_fn(**context):
    classifier_params = context["params"]["classifier"]
    if (
        not classifier_params.get("project_id")
        or not classifier_params.get("location")
        or not classifier_params.get("processor_id")
    ):
        logging.warning(
            f"Not all required parameters for the classifier are "
            f"provided (required `project_id`, `location` and "
            f"`processor_id`). {classifier_params=}"
        )
        raise AirflowSkipException()
    process_folder = context["ti"].xcom_pull(
        task_ids="initial_load_from_input_bucket.create_process_folder",
        key="process_folder",
    )
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
    process_folder = context["ti"].xcom_pull(
        task_ids="initial_load_from_input_bucket.create_process_folder",
        key="process_folder",
    )
    parsed_output = cloud_run_utils.read_classifier_job_output(
        process_bucket, process_folder, KNOWN_LABELS_FOR_CLASSIFIER
    )
    # context["ti"].xcom_push(key="classifier_output", value=parsed_output)
    return parsed_output


def data_store_import_docs(**context):
    data_store_region = os.environ.get("DPU_DATA_STORE_REGION")
    bq_table = context["ti"].xcom_pull(key="bigquery_table")

    operation_name = datastore_utils.import_docs_to_datastore(
        bq_table,
        data_store_region,
        os.environ.get("DPU_DATA_STORE_ID"),
    )
    return operation_name


def generate_update_doc_registry_job_params_fn(**context):
    bq_table = context["ti"].xcom_pull(key="bigquery_table")
    input_bq_table = (
        f"{bq_table['project_id']}.{bq_table['dataset_id']}."
        f"{bq_table['table_id']}"
    )
    process_folder = context["ti"].xcom_pull(
        task_ids="initial_load_from_input_bucket.create_process_folder",
        key="process_folder",
    )
    output_folder = f'{os.environ.get("DPU_PROCESS_BUCKET")}/{process_folder}/workflow-io/update_doc_registry'
    return cloud_run_utils.get_doc_registry_update_job_override(input_bq_table, output_folder)


def generate_process_job_params(**context):
    mv_params = context["ti"].xcom_pull(
        key="return_value",
        task_ids="initial_load_from_input_bucket.generate_files_move_parameters",
    )
    if not mv_params:
        logging.warning(
            "No need to run, since generate_files_move_parameters "
            "did not generate any files to process"
        )
        raise AirflowSkipException()
    bq_table = context["ti"].xcom_pull(key="bigquery_table")
    doc_processor_job_name = os.environ.get("DOC_PROCESSOR_JOB_NAME")
    gcs_reject_bucket = os.environ.get("DPU_REJECT_BUCKET")
    supported_files = {
        x["file-suffix"]: x["processor"] for x in context["params"]["supported_files"]
    }
    process_job_params = cloud_run_utils.get_process_job_params(
        bq_table, doc_processor_job_name, gcs_reject_bucket, mv_params, supported_files
    )
    return process_job_params


def generate_output_table_name(**context):
    process_folder = context["ti"].xcom_pull(key="process_folder")
    output_table_name = process_folder.replace("-", "_")
    context["ti"].xcom_push(key="output_table_name", value=output_table_name)


def generate_form_process_job_params(**context):
    # Build BigQuery table id <project_id>.<dataset_id>.<table_id>
    bq_table = context["ti"].xcom_pull(key="bigquery_table")

    # Build GCS input and out prefix -
    # gs://<process_bucket_name>/<process_folder>/pdf_forms/<input|output>
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
    render_template_as_native_obj=True,
    params={
        "input_bucket": os.environ.get("DPU_INPUT_BUCKET"),
        "process_bucket": os.environ.get("DPU_PROCESS_BUCKET"),
        "input_folder": "",
        "supported_files": Param(
            [
                {"file-suffix": "pdf", "processor": "txt-processor"},
                {"file-suffix": "docx", "processor": "txt-processor"},
                {"file-suffix": "txt", "processor": "txt-processor"},
                {"file-suffix": "html", "processor": "txt-processor"},
                {"file-suffix": "msg", "processor": "msg-processor"},
                {"file-suffix": "zip", "processor": "zip-processor"},
                # Default to out-of-box agent builder process for excel file,
                # but we still have our xlsx-processor, that does the conversion to txt,
                # as alternative for xlsx and xlsm
                {"file-suffix": "xlsx", "processor": "txt-processor"},
                {"file-suffix": "xlsm", "processor": "txt-processor"},
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
                "project_id": "",
                "location": "",
                "processor_id": "",
            },
            type="object",
            properties={
                "project_id": {"type": "string"},
                "location": {"type": "string"},
                "processor_id": {"type": "string"},
            },
            required=["project_id", "location", "processor_id"],
        ),
    },
) as dag:

    with TaskGroup(
        group_id="initial_load_from_input_bucket"
    ) as initial_load_from_input_bucket:
        list_all_input_files = GCSListObjectsOperator(
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

        short_circuit_move_rejected_files_if_any = ShortCircuitOperator(
            task_id="short_circuit_move_rejected_files_if_any",
            python_callable=lambda **context: context["ti"].xcom_pull(
                task_ids="initial_load_from_input_bucket.process_supported_types",
                key="files_to_reject",
            ),
            provide_context=True,
        )

        move_unsupported_files_to_rejected_bucket = GCSToGCSOperator(
            task_id="move_files_to_rejected_bucket",
            source_bucket="{{ params.input_bucket }}",
            source_objects="{{ ti.xcom_pull(task_ids='initial_load_from_input_bucket"
            ".process_supported_types', key='files_to_reject') }}",
            destination_bucket=os.environ.get("DPU_REJECT_BUCKET"),
            move_object=True,
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

        generate_check_duplicated_files_job_params = PythonOperator(
            task_id="generate_check_duplicated_files_job_params",
            python_callable=generate_check_duplicated_files_job_params_fn,
            provide_context=True,
        )

        check_duplicated_files = CloudRunExecuteJobOperator(
            project_id=os.environ.get("GCP_PROJECT"),
            # pyright: ignore[reportArgumentType]
            region=os.environ.get("DPU_REGION"),
            # pyright: ignore[reportArgumentType]
            task_id="check_duplicated_files",
            job_name=os.environ.get("DOC_REGISTRY_JOB_NAME"),
            # pyright: ignore[reportArgumentType]
            deferrable=False,
            overrides="{{ ti.xcom_pull("
            "task_ids='initial_load_from_input_bucket.generate_check_duplicated_files_job_params' "
            ", key='return_value') }}",
            # pyright: ignore[reportArgumentType]
        )

        move_duplicated_files_to_rejected_bucket = PythonOperator(
            task_id="move_duplicated_files_to_rejected_bucket",
            python_callable=move_duplicated_files_to_rejected_bucket_fn,
            provide_context=True,
        )

        has_files_to_process_after_removing_duplicates = BranchPythonOperator(
            task_id="has_files_to_process_after_removing_duplicates",
            python_callable=has_files_to_process_after_removing_duplicates_fn,
            provide_context=True,
        )

        skip_move_files = PythonOperator(
            task_id="skip_move_files",
            python_callable=lambda: print(
                "No file left after removing duplicates, processing ends here!"
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

    with TaskGroup(group_id="prep_for_processing") as prep_for_processing:
        create_output_table_name = PythonOperator(
            task_id="create_output_table_name",
            python_callable=generate_output_table_name,
            provide_context=True,
        )

        create_output_table = BigQueryCreateEmptyTableOperator(
            task_id="create_output_table",
            dataset_id=os.environ.get("DPU_OUTPUT_DATASET"),
            # pyright: ignore[reportArgumentType]
            table_id="{{ ti.xcom_pull("
            "task_ids='prep_for_processing.create_output_table_name', "
            "key='output_table_name') }}",
            schema_fields=[
                {"name": "id", "mode": "REQUIRED", "type": "STRING", "fields": []},
                {
                    "name": "jsonData",
                    "mode": "NULLABLE",
                    "type": "STRING",
                    "fields": [],
                },
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

    with TaskGroup(group_id="classify_pdfs") as classify_pdfs:
        generate_classify_job_params = PythonOperator(
            task_id="generate_classify_job_params",
            python_callable=generate_classify_job_params_fn,
            provide_context=True,
        )

        execute_doc_classifier = CloudRunExecuteJobOperator(
            project_id=os.environ.get("GCP_PROJECT"),
            # pyright: ignore[reportArgumentType]
            region=os.environ.get("DPU_REGION"),
            # pyright: ignore[reportArgumentType]
            task_id="execute_doc_classifier",
            job_name=os.environ.get("DOC_CLASSIFIER_JOB_NAME"),
            # pyright: ignore[reportArgumentType]
            deferrable=False,
            overrides="{{ ti.xcom_pull("
            "task_ids='classify_pdfs.generate_classify_job_params' "
            ", key='return_value') }}",
            # pyright: ignore[reportArgumentType]
        )

        parse_doc_classifier_results_and_move_files = PythonOperator(
            task_id="parse_doc_classifier_results_and_move_files",
            python_callable=parse_doc_classifier_output,
            provide_context=True,
        )

        classified_docs_moved_or_skipped = DummyOperator(
            task_id="classified_docs_moved_or_skipped",
            trigger_rule=TriggerRule.ALL_DONE,
        )

    with TaskGroup(group_id="general_processing") as general_processing:
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

        generate_update_doc_registry_job_params = PythonOperator(
            task_id="generate_update_doc_registry_job_params",
            python_callable=generate_update_doc_registry_job_params_fn,
            execution_timeout=timedelta(seconds=3600),
            provide_context=True,
        )

        update_doc_registry = CloudRunExecuteJobOperator(
            project_id=os.environ.get("GCP_PROJECT"),
            region=os.environ.get("DPU_REGION"),
            task_id="update_doc_registry",
            job_name=os.environ.get("DOC_REGISTRY_JOB_NAME"),
            deferrable=False,
            overrides="{{ ti.xcom_pull("
            "task_ids='general_processing.generate_update_doc_registry_job_params' "
            ", key='return_value') }}",
        )

    with TaskGroup(group_id="forms_processing") as forms_processing:
        create_form_process_job_params = PythonOperator(
            task_id="create_form_process_job_params",
            python_callable=generate_form_process_job_params,
            provide_context=True,
        )

        execute_forms_parser = CloudRunExecuteJobOperator(
            # Calling os.environ[] instead of using the .get method to verify we
            # have set environment variables, not allowing None values.
            project_id=os.environ["GCP_PROJECT"],
            region=os.environ["DPU_REGION"],
            task_id="execute_forms_parser",
            job_name=os.environ["FORMS_PARSER_JOB_NAME"],
            deferrable=False,
            overrides=(
                "{{ ti.xcom_pull(task_ids='forms_processing.create_form_process_job_params', key='return_value') }}"
            ),
            # pyright: ignore[reportArgumentType]
        )

        import_forms_to_data_store = PythonOperator(
            task_id="import_forms_to_data_store",
            python_callable=data_store_import_docs,
            execution_timeout=timedelta(seconds=3600),
            provide_context=True,
        )

    (  # pyright: ignore[reportUnusedExpression, reportOperatorIssue]
        # initial common actions - ends with a decision whether to continue
        # to basic processing, or stop working
        list_all_input_files
        >> process_supported_types
        >> [short_circuit_move_rejected_files_if_any, has_files]
    )

    (  # pyright: ignore[reportUnusedExpression, reportOperatorIssue]
        short_circuit_move_rejected_files_if_any
        >> move_unsupported_files_to_rejected_bucket
    )
    (  # pyright: ignore[reportUnusedExpression, reportOperatorIssue]
        has_files >> [create_process_folder, skip_bucket_creation]
    )
    (  # pyright: ignore[reportUnusedExpression, reportOperatorIssue]
        # In the case we continue working, moving documents to processing
        # folder, and creating an output table where metadata will be saved
        create_process_folder
        >> generate_check_duplicated_files_job_params
        >> check_duplicated_files
        >> move_duplicated_files_to_rejected_bucket
        >> has_files_to_process_after_removing_duplicates
        >> [generate_files_move_parameters, skip_move_files]
    )
    (   # pyright: ignore[reportUnusedExpression, reportOperatorIssue]
        generate_files_move_parameters
        >> move_to_processing
        >> create_output_table_name
        >> create_output_table
    )
    (  # pyright: ignore[reportUnusedExpression, reportOperatorIssue]
        # We then want to see if there are any forms, since those will be
        # handled differently.
        create_output_table
        >> generate_classify_job_params
        >> execute_doc_classifier
        >> parse_doc_classifier_results_and_move_files
        >> classified_docs_moved_or_skipped
    )
    (  # pyright: ignore[reportUnusedExpression, reportOperatorIssue]
        # Continue to process forms, depending on move_forms executed
        # successfully. This doesn't have to wait for general processing.
        parse_doc_classifier_results_and_move_files
        >> create_form_process_job_params
        >> execute_forms_parser
        >> import_forms_to_data_store
    )
    (  # pyright: ignore[reportUnusedExpression, reportOperatorIssue]
        # General document processing has to wait for the forms to
        # move/skipped, since we don't want to process the forms using this job.
        classified_docs_moved_or_skipped
        >> create_process_job_params
        >> execute_doc_processors
        >> [import_docs_to_data_store, generate_update_doc_registry_job_params]
    )
    (   # pyright: ignore[reportUnusedExpression, reportOperatorIssue]
        # update the document registry with the newly ingested documents
        generate_update_doc_registry_job_params
        >> update_doc_registry
    )
