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

variable "alloy_db_cluster_id" {
  description = "AlloyDB Cluster ID"
  type        = string
  default     = "eks-docs-results"
}

variable "artifact_repo" {
  description = "Docker registry"
  type        = string
  default     = ""
}

variable "doc_deletion_cloud_run_job_name" {
  description = "Doc Deletion job name"
  type        = string
  default     = "delete-docs"
}

variable "serverless_connector_subnet" {
  description = "Name of the VPC subnet to create"
  type        = string
}

variable "alloydb_database" {
  description = "AlloyDB Database"
  type        = string
  default     = "postgres"
}

variable "vpc_network_name" {
  type        = string
  description = "The name of the network where subnets will be created"
}

variable "alloydb_primary_instance" {
  description = "alloydb primary instance id"
  type        = string
}

variable "alloydb_cluster_ready" {
  description = "creating the alloydb resource in terraform does not guarantee it's in the ready state, so subsequent steps fail. This resource exists to force a sleep_timer that is referencable from other modules, and must be passed as a variable into this module (instead of depends_on) because the gcloud submodule has errors related to `depends_on` block. See: https://github.com/kingman/tf-dont-do-depends-on-module-demo/blob/main/demo-flow/README.md"
  type        = bool
}

variable "cloud_build_service_account_email" {
  description = "the user-managed service account configured for Cloud Build"
  type        = string
}

variable "data_store_project_id" {
  description = "The project id for the Vertex AI Data Store"
  type        = string
}

variable "data_store_region" {
  description = "The region for the Vertex AI Data Store"
  type        = string
}

variable "data_store_collection" {
  description = "The collection for the Vertex AI Data Store"
  type        = string
  default     = "default_collection"
}

variable "data_store_id" {
  description = "The id for the Vertex AI Data Store"
  type        = string
}

variable "data_store_branch" {
  description = "The branch for the Vertex AI Data Store"
  type        = string
  default     = "default_branch"
}

variable "bq_processed_documents_table_name" {
  type = string
  description = "The BigQuery table name for the processed documents"
}
