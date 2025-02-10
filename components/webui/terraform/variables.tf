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
  description = "Google Cloud region where resources are located "
}

variable "artifact_repo" {
  description = "Docker registry"
  type        = string
}

variable "cloud_build_service_account_email" {
  description = "IAM service account email used for cloud build."
  type        = string
}

variable "iap_access_domains" {
  description = "List of domains granted for IAP access to the APP"
  type        = list(string)
}

variable "vertex_ai_data_store_region" {
  description = "The geographic location where the data store should reside. The value can only be one of 'global', 'us' and 'eu'"
  type        = string
}

variable "agent_builder_data_store_id" {
  description = "Data store used"
  type        = string
}

variable "agent_builder_search_id" {
  description = "Agent builder search engine id"
  type        = string
}

variable "webui_service_name" {
  type        = string
  description = "The service name for the webui"
  default     = "eks-ui"
}

variable "lb_ssl_certificate_domains" {
  description = "Custom domain pointing to the WebUI app, DNS configured"
  type        = list(string)
}

variable "vpc_network_name" {
  type        = string
  description = "The name of the network where subnets will be created"
}

variable "serverless_connector_subnet" {
  description = "Name of the VPC subnet to create"
  type        = string
}
