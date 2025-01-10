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

variable "configure_schema_cloud_run_job_name" {
  description = "Configure db schemas and permissions in AlloyDB"
  type        = string
  default     = "configure-db-schema"
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

variable "additional_db_users" {
  description = "The AlloyDB db roles associated with the service accounts identities that requires access to eks data."
  type        = list(string)
}

variable "db_role_content_hash" {
  description = "Additional deployment trigger to force rerun module.gcloud_build_job_to_configure_alloydb_schema if terraform reverts the db roles on specialized_parser_role (flaky)"
  type        = string
}

variable "vpc_access_connector_id" {
  type = string
}