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

output "project_id" {
  description = "Google Cloud project user by the module."
  value       = module.project_services.project_id
}

output "bq_registry_dataset_id" {
  description = "BigQuery document registry dataset"
  value       = module.docs_registry_dataset.bigquery_dataset.dataset_id
}

output "bq_registry_table_id" {
  description = "BigQuery document registry table"
  value       = module.docs_registry_dataset.table_ids[0]   
}

output "doc_registry_service_cloud_run_job_name" {
  description = "Doc Registry service job name"
  value       = google_cloud_run_v2_job.doc-registry-service-job.name
}
