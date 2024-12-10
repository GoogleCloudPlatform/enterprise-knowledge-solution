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
  description = "Cloud region where the resources are deployed"
}

variable "vertex_ai_data_store_region" {
  description = "The geographic location where the data store should reside. The value can only be one of 'global', 'us' and 'eu'"
  type        = string
}

variable "iap_access_domains" {
  description = "List of domains granted for IAP access to the APP"
  type        = list(string)
}

variable "docai_location" {
  description = "Google Cloud region where compute services are located."
  type        = string
  default     = "us"
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

variable "webui_domains" {
  description = "Custom domain pointing to the WebUI app, DNS configured"
  type        = list(string)
}

variable "custom_classifier_id" {
  description = "The Custom DocAI classifier to classify PDFs. If no classifier is specified, no specialized processors will be triggered. Format: `projects/PROJECT_ID/locations/LOCATION/processors/PROCSESOR_ID"
  type        = string
  default     = ""
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
  default = {
    subnet_primary           = "10.10.10.0/24"
    cluster_secondary_range  = "10.154.0.0/17"
    services_secondary_range = "10.154.128.0/22"
    control_plane            = "172.31.245.0/24"
    sql                      = "10.0.0.0/12"
  }
}

variable "serverless_connector_subnet" {
  description = "Name of the VPC subnet to create"
  type        = string
  default     = "cloudrun-to-alloydb-connector-subnet"
}

variable "serverless_connector_subnet_range" {
  description = "Range of the VPC subnet to create"
  type        = string
  default     = "10.2.0.0/16"
}

variable "psa_reserved_address" {
  description = "First address of CIDR range to reserve for the Private Services Access connection used by AlloyDB. The prefix_length is configured separately in terraform."
  type        = string
  default     = "10.11.0.0"
}
