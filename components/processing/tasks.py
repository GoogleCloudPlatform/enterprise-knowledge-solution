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

from invoke import task


# Find the base directory for invoke
BASE_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.join(BASE_DIR, "../../")


@task
def cloud_run_remote_build(c):
    """Document Processor builder with Cloud Build (Cloud Run)

    This will build and deploy a new instance of Cloud Run
    using Cloud Build.
    """
    with c.cd(ROOT_DIR):
        c.run(
            "gcloud builds submit "
            f"--region {os.getenv('REGION')} "
            f"--project {os.getenv('PROJECT_ID')} "
            "--config \"components/processing/deployments/cloud_run/build/cloudbuild.yaml\" .",
            pty=True,
        )


@task
def cloud_run_local_deploy(c):
    """Document Processor local deployer (Cloud Run)

    This will deploy a new instance of Cloud Run jobs from the local
    codebase. This will use the local docker and gcloud commands
    to deploy.
    """
    repo = (
        f"{os.getenv('REPOSITORY_REGION')}-docker.pkg.dev/"
        f"{os.getenv('PROJECT_ID')}/{os.getenv('ARTIFACT_REPO_NAME')}"
    )
    job_name = os.getenv("CLOUD_RUN_JOB_NAME")
    image = f"{repo}/{job_name}:latest"

    with c.cd(BASE_DIR):
        c.run(
            f"docker buildx build "
            "--push "
            f"--build-context libs=libs "
            f"--build-context reqs={ROOT_DIR}/reqs "
            f"-t {image} "
            f"deployments/cloud_run/build",
            pty=True,
        )
        c.run(
            f"gcloud "
            f"--project {os.getenv('PROJECT_ID')} "
            f"run jobs "
            f"--region {os.getenv('REGION')} "
            f"deploy {job_name} "
            f"--task-timeout=60m "
            f"--service-account={os.getenv('SERVICE_ACCOUNT')} "
            f"--image={image}"
        )


@task(
    help={
        "process-dir": "Folder of input objects to process",
    },
)
def cloud_run_execute(
    c, process_dir, reject_dir, with_html=True, write_json=True, write_bigquery=""
):
    """Document Processor execute (Cloud Run)

    This will execute a previously deployed Cloud Run Document
    Processor instance with the specified parameters. It can only
    operate on GCS objects, but will run in a Cloud run environment.
    """
    with c.cd(BASE_DIR):
        c.run(
            "gcloud run jobs "
            f"--region {os.getenv('REGION')} "
            f"--project {os.getenv('PROJECT_ID')} "
            f"execute doc-processor "
            f"--args {process_dir},"
            f"--reject_dir={reject_dir},"
            f"--with_html={with_html},"
            f"--write_json={write_json},"
            f"--write_bigquery={write_bigquery}"
        )


@task(
    help={
        "process-dir": "Folder of input objects to process",
    },
)
def process(
    c,
    process_dir,
    reject_dir,
    with_html=True,
    write_json=True,
    write_bigquery="",
    debug=True,
):
    """Document Processor (development)

    This will apply the Document Processor to the
    specified processor and run on the development machine.

    It will operate on GCS or local files as specified.
    """
    from processors.base.gcsio import GCSPath
    from processors.msg.main_processor import process_all_objects
    import logging

    logging.basicConfig(format="%(asctime)s %(name)s: %(message)s")
    logging.getLogger("processors").setLevel(logging.DEBUG if debug else logging.INFO)

    # Process everything
    process_all_objects(
        GCSPath(process_dir),
        GCSPath(reject_dir),
        with_html=with_html,
        write_json=write_json,
        write_bigquery=write_bigquery,
    )
