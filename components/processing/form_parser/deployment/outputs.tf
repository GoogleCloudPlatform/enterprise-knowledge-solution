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

output "form_parser_cloud_run_job_name" {
  description = "Cloud Run form parser job name"
  value       = var.form_parser_cloud_run_job_name
}

output "form_parser_service_account" {
  description = "Service Account used for handling form parsing jobs."
  value       = google_service_account.dpu_run_service_account.email
}
