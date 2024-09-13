
# Cloud Run Deployment

## Overview

The Cloud Run deployment is intended to provide a Cloud Run Job for execution on an
as-needed basis against a processing folder.

Orchestration of incremental updates is and updating of AI Agent Builder is intended
to be done outside of this code.

## Deploying Cloud Run

### Create a project

Create a project that will run with Cloud Run enabled. Terraform is provided to do
this, along with create a artifact repository.

### Run invoke.sh 

Run `../../invoke.sh cloud-run.deploy` or `../../invoke.sh cloud-run.cloud-build` depending
if cloud build is intended to be used or a local docker build.
