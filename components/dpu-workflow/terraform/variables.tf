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

variable "required_apis" {
  type        = list(any)
  description = "list of required GCP services"
  default     = ["composer.googleapis.com"]
}

variable "vpc_network_name" {
  type        = string
  description = "The name of the network where subnets will be created"
}

variable "vpc_network_id" {
  type        = string
  description = "ID of the network where subnets will be created"
}

variable "region" {
  type        = string
  description = "Cloud region where the workflow resources is created"
}

variable "composer_version" {
  description = "Version of Cloud Composer"
  type        = string
  default     = "composer-3-airflow-2.9.3-build.11"
}

variable "composer_env_variables" {
  description = "Environment variables to set in the Composer environment"
  type        = map(any)
}

variable "composer_additional_pypi_packages" {
  description = "Additional PyPI packages add to the Composer environment"
  type        = map(any)
  default = {
    google-cloud-discoveryengine = ">=0.11.11"
  }
}

variable "composer_scheduler_cpu" {
  description = "The number of CPUs for a scheduler, in vCPU units."
  type        = number
  default     = 1
}

variable "composer_scheduler_memory" {
  description = "The amount of memory for a scheduler, in GB."
  type        = number
  default     = 2
}

variable "composer_scheduler_storage" {
  description = "The disk size for a scheduler, in GB."
  type        = number
  default     = 1
}

variable "composer_scheduler_count" {
  description = "The number of schedulers."
  type        = number
  default     = 1
}

variable "composer_web_server_cpu" {
  description = "The number of CPUs for a web_server, in vCPU units."
  type        = number
  default     = 1
}

variable "composer_web_server_memory" {
  description = "The amount of memory for a web_server, in GB."
  type        = number
  default     = 2
}

variable "composer_web_server_storage" {
  description = "The disk size for a web_server, in GB."
  type        = number
  default     = 1
}

variable "composer_worker_cpu" {
  description = "The number of CPUs for a worker, in vCPU units."
  type        = number
  default     = 1
}

variable "composer_worker_memory" {
  description = "The amount of memory for a worker, in GB."
  type        = number
  default     = 4
}

variable "composer_worker_storage" {
  description = "The disk size for a worker, in GB."
  type        = number
  default     = 2
}

variable "composer_worker_min_count" {
  description = "The minimum number of Airflow workers."
  type        = number
  default     = 1
}

variable "composer_worker_max_count" {
  description = "The maximum number of Airflow workers."
  type        = number
  default     = 3
}

variable "composer_environment_size" {
  description = "Size for the Composer environment"
  type        = string
  default     = "ENVIRONMENT_SIZE_SMALL"
}

variable "composer_sa_roles" {
  type        = list(any)
  description = "list of required roles for the Composer service account"
  default = [
    "roles/composer.worker",
    "roles/iam.serviceAccountUser",
    "roles/bigquery.dataEditor",
    "roles/run.developer",
    "roles/discoveryengine.editor",
  ]
}

variable "composer_cidr" {
  description = "CIDR ranges for configuring Cloud Composer"
  type = object({
    subnet_primary = string
  })
}

variable "composer_connector_subnet" {
  description = "Name of the VPC subnet used for VPC connectivity to Composer 3 in a service producer project"
  type        = string
  default     = "composer-subnet"
}
