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
  type        = string
  description = "project id required"
}

variable "region" {
  type        = string
  description = "Cloud region where the resources are created"
}

variable "bq_registry_dataset" {
  description = "BigQuery dataset"
  type        = string
  default     = "docs_registry"
}

variable "bq_registry_table" {
  description = "BigQuery table for aggregated doument registry"
  type        = string
  default     = "docs_registry"
}

variable "doc_registry_service_cloud_run_job_name" {
  description = "Doc registry service job name"
  type        = string
  default     = "doc-registry-service"
}

variable "artifact_repo" {
  description = "Docker registry"
  type        = string
  default     = ""
}

variable "cloud_build_service_account_email" {
  description = "the user-managed service account configured for Cloud Build"
  type        = string
}
