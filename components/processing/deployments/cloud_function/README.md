
# Cloud Function Deployment

## Overview

The Cloud Function deployment is intended to enable an easy proof of concept
and evaluation.

For example, incremental updates between batches is possible but code not included
as part of this deployment.

## Deploying the Function

### Create a project

Create a project that will run with BigQuery and Cloud Functions enabled.

A number of services and permissions will likely need to be enabled.

### Customise and run deploy.sh

Change the following parameters in deploy.sh:
```
PROJECT_ID=<project>
REGION=<region for Cloud Function>
GCS_LOCATION=<region for GCS bucket>
BQ_LOCATION=<region for BigQuery dataset>
```

The [deploy.sh](deploy.sh) script will:

 * Create a bucket if needed
 * Create the destination table for writing the results
 * Deploy the Cloud Function with the parameters

## Use the Function

It is suggested to use the function with a notion of 'batch' or set of files to use.

### Copy the inputs

For example, copying across .msg files:

```sh
gsutil -m cp *.msg <bucket>/input/<batchId>/
```

### Monitoring the Progress

The Cloud Function logs will show the activity or if something is not working.

The Cloud Function will move objects from <bucket>/input/<batchId> to <bucket>/output/<batchId>, and create more objects within the same folder. These should be easy to observe.

### Indexing with Agent Builder

For the Agent Builder datastore, specify the `<project>.processing.processed` table. This will be for a full index.

For incremental index, it is suggested to create a temporary table filtering out URI objects of just the <batchId> you wish to process and use the temporary table with Agent Builder.