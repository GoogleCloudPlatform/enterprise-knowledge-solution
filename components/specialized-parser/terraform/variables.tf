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
  description = "Google Cloud project where infrastructure resource are deployed"
  type        = string
}

variable "region" {
  description = "Google Cloud region where compute services are located."
  type        = string
}

variable "artifact_repo" {
  description = "Docker registry"
  type        = string
}

variable "specialized_parser_cloud_run_job_name" {
  description = "Specialized Parser job name"
  type        = string
}

variable "bigquery_dataset_id" {
  description = "BigQuery Dataset id"
  type        = string
}

variable "alloydb_instance" {
  description = "AlloyDB Instance"
  type        = string
}

variable "alloydb_database" {
  description = "AlloyDB Database"
  type        = string
  default     = "postgres"
}

variable "processors_location" {
  description = "Location to setup Document AI processors"
  type        = string
  default     = "us"
}

variable "network" {
  description = "Name of the VPC network to use"
  type        = string
}

variable "serverless_connector_subnet" {
  description = "Name of the VPC subnet to create"
  type        = string
}

variable "cloud_build_service_account_email" {
  description = "the user-managed service account configured for Cloud Build"
  type        = string
}
