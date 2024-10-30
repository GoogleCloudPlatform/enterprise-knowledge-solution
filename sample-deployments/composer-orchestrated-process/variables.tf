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

variable "webui_service_name" {
  type        = string
  description = "Specify the WebUI App Engine service name, use the default value when doing initial deployment. Change the default value after the initial deployment and re-apply terraform"
  default     = "default"
}

variable "docai_location" {
  description = "Google Cloud region where compute services are located."
  type        = string
  default     = "us"
}

variable "create_vpc_network" {
  type = bool
  description = "configuration to manage vpc creation"
  default = true
}

variable "vpc_name" {
  type = string
  description = "name of vpc network"
  default = "dpu-network"
}

variable "vpc_id" {
  type = string
  description = "id of vpc network"
  default = ""
}

variable "webui_domains" {
  description = "Custom domain pointing to the WebUI app, DNS configured"
  type        = list(string)
}
