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
variable "htil_api_endpoint" {
  type = string
  description = "The API endpoint to access the HTIL api"
}

variable "adpui_service_name" {
  type        = string
  description = "The service name for the adpui"
  default     = "eks-adp-ui"
}

variable "lb_ssl_certificate_domains" {
  description = "Custom domain pointing to the ADP UI app, DNS configured"
  type        = list(string)
}

variable "iap_client_id" {
  type = string
  description = "The IAP Oauth Client ID"
}

variable "iap_secret" {
  type = string
  sensitive = true
  description = "The IAP Oauth Client secret"
}

variable "iap_member" {
  type = string
  description = "The IAP member"
}

variable "ssl_policy_link" {
  type = string
  description = "SSL Policy Self Link for LB"
}
