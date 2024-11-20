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

variable "bq_store_dataset" {
  description = "BigQuery dataset"
  type        = string
  default     = "docs_store"
}

variable "create_vpc_network" {
  type        = bool
  description = "configuration to manage vpc creation"
  default     = true
}

variable "vpc_name" {
  type        = string
  description = "name of vpc network"
  default     = "dpu-network"
}

variable "alloy_db_cluster_id" {
  description = "AlloyDB Cluster ID"
  type        = string
  default     = "eks-docs-results"
}

variable "composer_cidr" {
  description = "CIDR ranges for configuring Cloud Composer"
  type = object({
    subnet_primary           = string
    cluster_secondary_range  = string
    services_secondary_range = string
    control_plane            = string
    sql                      = string
  })
}

variable "serverless_connector_subnet" {
  description = "Name of the VPC subnet to create"
  type        = string
  default     = "cloudrun-to-alloydb-connector-subnet"
}

variable "serverless_connector_subnet_range" {
  description = "Range of the VPC subnet to create"
  type        = string
  default     = "10.2.0.0/24"
}


variable "specialized_parser_cloud_run_job_name" {
  description = "Specialized Parser job name"
  type        = string
  default     = "specialized-parser-job"
}
