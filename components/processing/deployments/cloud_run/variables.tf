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

variable "project_id" {
  description = "Google Cloud project where infracture resource such as BigQuery dataset and Artifact repository are deployed"
  type        = string
}

variable "region" {
  description = "Google Cloud region where compute services are located."
  type        = string
}

variable "bq_region" {
  description = "Google Cloud region where BigQuery data is stored."
  type        = string
}

variable "gcs_region" {
  description = "Google Cloud region where GCS data is stored."
  type        = string
}

variable "repository_region" {
  description = "Google Cloud region where container images are stored."
  type        = string
}

variable "artifact_repo_name" {
  description = "Docker registry"
  type        = string
  default     = ""
}

variable "cloud_run_job_name" {
  description = "Doc processor job name"
  type        = string
  default     = "doc-processor"
}
