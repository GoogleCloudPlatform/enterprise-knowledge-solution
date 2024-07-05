#!/bin/bash
#
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

DEPLOY_DIR="$(realpath $(dirname $0))"


#
# Sample deployment function
#

# Change these parameters as suitable for you
# PROJECT_ID=fsi-scratch-7
# REGION=europe-west1
# GCS_LOCATION=eu
# BQ_LOCATION=eu

# PROJECT_ID=dpu-demo
# REGION=us-central1
# GCS_LOCATION=us-central1
# BQ_LOCATION=us-central1

# TRUE - more detail, FALSE - less detail
DEBUG=TRUE

#
# Enable the required services
#
gcloud --project ${PROJECT_ID} services enable \
  logging cloudbuild.googleapis.com cloudfunctions.googleapis.com \
  pubsub.googleapis.com bigquery.googleapis.com run.googleapis.com \
  eventarc.googleapis.com > /dev/null


#
# Grant required access to the service accounts
# 
# See https://cloud.google.com/eventarc/docs/run/create-trigger-storage-gcloud
# for some background on the permissions
#

# Grant access to the default compute account
PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(projectNumber)")
COMPUTE_SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
# This is used for receiving eventArc messages
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${COMPUTE_SERVICE_ACCOUNT}" \
  --role=roles/eventarc.eventReceiver > /dev/null
# This is used for invoking Cloud Run from Pub/Sub messages
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${COMPUTE_SERVICE_ACCOUNT}" \
  --role=roles/run.invoker > /dev/null
# This is used for writing to the BigQuery table (processed)
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${COMPUTE_SERVICE_ACCOUNT}" \
  --role=roles/bigquery.dataEditor > /dev/null
# This is used for reading/writing processed objects
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${COMPUTE_SERVICE_ACCOUNT}" \
  --role=roles/storage.objectUser > /dev/null

# Grant acccess to the storage account
# This is required for EventArc to publish into Pub/Sub (used as part of Cloud Function)
STORAGE_SERVICE_ACCOUNT="$(gsutil kms serviceaccount -p ${PROJECT_ID})"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${STORAGE_SERVICE_ACCOUNT}" \
    --role=roles/pubsub.publisher > /dev/null


#
# Create the bucket
#
BUCKET=${PROJECT_ID}-doc-processing-bucket
if gsutil ls -L gs://${BUCKET} > /dev/null 2>&1; then
  echo "Bucket exists ${BUCKET}"
else
  gsutil mb -p ${PROJECT_ID} -l ${GCS_LOCATION}  gs://${BUCKET}
fi


#
# Create the destination table
# 
DATASET_ID=processing
BUCKET_OUTPUT=gs://${BUCKET}/output
cat << "EOF" | sed \
  -e "s/\${PROJECT_ID}/${PROJECT_ID}/g" \
  -e "s/\${DATASET_ID}/${DATASET_ID}/g" \
  -e "s/\${BQ_LOCATION}/${BQ_LOCATION}/g" | \
  bq \
    --location ${BQ_LOCATION} \
    query \
    --nouse_legacy_sql \
    --project_id ${PROJECT_ID} \
    --max_rows 0

CREATE SCHEMA IF NOT EXISTS `${PROJECT_ID}.${DATASET_ID}` OPTIONS (
  location = '${BQ_LOCATION}'
);

CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.${DATASET_ID}.processed`
(
  id STRING NOT NULL OPTIONS(description="ID of the source parsing entity"),
  jsonData STRING OPTIONS(description="Parsed output metadata JSON"),
  content STRUCT<
    mimeType STRING OPTIONS(description="mimeType of content"),
    uri STRING OPTIONS(description="Object URI")
  >
)
OPTIONS(
  description="Object processing table"
);
EOF

#
# Deploy the Cloud Function
#

INPUT_PREFIX=input/
(
  # Move to deploy directory
  cd "${DEPLOY_DIR}"

  # Update libraries if not packaged
  if [ -f "package.sh" ]; then
    mkdir "./libs"
    cp -r ../../libs/* ./libs
  fi

  # See for some of the patterns that can be used for event filters
  # https://cloud.google.com/eventarc/docs/path-patterns
  gcloud --project ${PROJECT_ID} functions deploy doc-processor \
    --gen2 \
    --trigger-event-filters="type=google.cloud.storage.object.v1.finalized" \
    --trigger-event-filters="bucket=${BUCKET}" \
    --region=${REGION} \
    --runtime=python311 \
    --source=. \
    --memory=1024MB \
    --entry-point=process_gcs \
    --trigger-location=${GCS_LOCATION} \
    --set-env-vars=DEBUG=${DEBUG},PROCESS_BUCKET=${BUCKET_OUTPUT},BQ_RESULTS_TABLE=${PROJECT_ID}.${DATASET_ID}.processed,GCS_PREFIX=${INPUT_PREFIX}

  # Delete libraries afterwards (don't create confusion) if not packaged
  if [ -f "package.sh" ]; then
    rm -rf ./libs
  fi
)
