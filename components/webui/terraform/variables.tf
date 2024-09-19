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
  description = "Google Cloud region where app engine is located "
}

variable "artifact_repo" {
  description = "artifact registry"
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

variable "gcs_object_store" {
  type        = string
  description = "GCS bucket for objects viewed through webui"
}

variable "webui_service_name" {
  type        = string
  description = "The App Engine service name for the webui"
}

variable "lb_ssl_certificate_domains" {
  description = "Custom domain pointing to the WebUI app, DNS configured"
  type        = list(string)
}
