#!/usr/bin/env bash

# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

## remove this after debugging
export TEST_PROJECT_ID=eks-int-75f65a8
##

gcloud storage cp gs://"$PROJECT_ID"-testdocs/EKS_Test_Scenarios/GoogleQuarterlyResults/* gs://docs-input-"$TEST_PROJECT_ID"/
gcloud storage cp gs://"$PROJECT_ID"-testdocs/EKS_Test_Scenarios/Test0_Demo_PDFs/* gs://docs-input-"$TEST_PROJECT_ID"/
gcloud storage cp gs://"$PROJECT_ID"-testdocs/EKS_Test_Scenarios/Test1_Text_Only_PDFs/* gs://docs-input-"$TEST_PROJECT_ID"/
gcloud storage cp gs://"$PROJECT_ID"-testdocs/EKS_Test_Scenarios/Test2_PDFs_With_Forms/* gs://docs-input-"$TEST_PROJECT_ID"/
gcloud storage cp gs://"$PROJECT_ID"-testdocs/EKS_Test_Scenarios/Test3_XLS/* gs://docs-input-"$TEST_PROJECT_ID"/
gcloud storage cp gs://"$PROJECT_ID"-testdocs/EKS_Test_Scenarios/Test4_MSG/* gs://docs-input-"$TEST_PROJECT_ID"/
gcloud storage cp gs://"$PROJECT_ID"-testdocs/EKS_Test_Scenarios/TEST5_DOCX_Files/* gs://docs-input-"$TEST_PROJECT_ID"/
gcloud storage cp gs://"$PROJECT_ID"-testdocs/EKS_Test_Scenarios/Test6_EDI_TXT/* gs://docs-input-"$TEST_PROJECT_ID"/
gcloud storage cp gs://"$PROJECT_ID"-testdocs/EKS_Test_Scenarios/Zebra/* gs://docs-input-"$TEST_PROJECT_ID"/
