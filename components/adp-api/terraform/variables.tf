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

variable "adpapi_service_name" {
  type        = string
  description = "The service name for the adpapi"
  default     = "adp-api"
}

variable "iap_member" {
  type        = string
  description = "The IAP member"
}

variable "serverless_connector_subnet" {
  description = "Name of the VPC subnet to create"
  type        = string
}

variable "vpc_network_name" {
  type        = string
  description = "The name of the network where subnets will be created"
}

variable "adp_ui_url" {
  type        = string
  description = "The URL for the UI that calls this API"
}

variable "lb_backend_services" {
  type        = map(any)
  description = "Backend services for the common land balancer, used to apply granular access controls for each Cloud Run Service through IAP"
}

variable "iap_access_groups" {
  description = "Google Groups that will grant persona access to the relevant web UIs, in the string format 'group:foo@example.com' or 'user:foo@example.com'."
  type = object({
    domain   = string
    reader   = string
    uploader = string
    operator = string
  })
}
