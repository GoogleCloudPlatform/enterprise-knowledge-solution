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

output "doc_deletion_cloud_run_job_name" {
  description = "Cloud Run doc deletion job name"
  value       = google_cloud_run_v2_job.doc_deletion_job.name
}

output "doc_deletion_service_account" {
  description = "Doc deletion service account"
  value       = module.doc_deletion_account.email
}

output "doc_deletion_db_user" {
  description = "The AlloyDB db role associated with the service account identity of the doc deletion Cloud Run job"
  value       = google_alloydb_user.doc_deletion_db_user.user_id
}

output "db_role_content_hash" {
  description = "Additional deployment trigger to force rerun module.gcloud_build_job_to_configure_alloydb_schema if terraform reverts the db roles on specialized_parser_role (flaky)"
  value       = sha512(terraform_data.dbrole_deployment_trigger.id)
}
