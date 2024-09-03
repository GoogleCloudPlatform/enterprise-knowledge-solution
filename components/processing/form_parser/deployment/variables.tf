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
  description = "Google Cloud project where infracture resource such as BigQuery dataset and Artifact repository are deployed"
  type        = string
}

variable "region" {
  description = "Google Cloud region where compute services are located."
  type        = string
  default     = "us-central1"
}

variable "location" {
  description = "Google Cloud region where compute services are located."
  type        = string
  default     = "us"
}

variable "docai_form_processor_name" {
  description = "Google Cloud region where compute services are located."
  type        = string
  default     = "dpu-docai-form-processor-2"
}

variable "dpu_run_service_account" {
  description = "Value of the Service Account Id for Cloud Run Job running DocAI Form Parser"
  type        = string
  default     = "dpu-form-parser-sa"
}

variable "dpu_run_service_account_display_name" {
  description = "Value of the Service Account name for Cloud Run Job running DocAI Form Parser"
  type        = string
  default     = "service account name for Cloud Run Job running DocAI Form Parser"
}

variable "form_parser_cloud_run_job_name" {
  description = "Google Cloud region where compute services are located."
  type        = string
  default     = "dpu-form-parser"
}

variable "gcs_output_prefix" {
  description = "Google Cloud region where compute services are located."
  type        = string
  default     = "gs://doc-ai-processor/output-forms/"
}

variable "gcs_input_prefix" {
  description = "Google Cloud region where compute services are located."
  type        = string
  default     = "gs://doc-ai-processor/input-forms/"
}
