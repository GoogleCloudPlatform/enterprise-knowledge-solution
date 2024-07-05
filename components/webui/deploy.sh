#!/bin/bash

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


gcloud run deploy "$SERVICE_NAME" \
  --port=8080 \
  --image="$AR_REPO_LOCATION-docker.pkg.dev/$GOOGLE_CLOUD_PROJECT/$AR_REPO/$SERVICE_NAME" \
  --allow-unauthenticated \
  --region=$AR_REPO_LOCATION \
  --platform=managed  \
  --project=$GOOGLE_CLOUD_PROJECT \
  --set-env-vars=GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,AR_REPO_LOCATION=$AR_REPO_LOCATION,LOCATION=$LOCATION,GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,SEARCH_DATASTORE_ID=$SEARCH_DATASTORE_ID,SEARCH_APP_ID=$SEARCH_APP_ID,LLM_LOCATION=$LLM_LOCATION,LLM=$LLM