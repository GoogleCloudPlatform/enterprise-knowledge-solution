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

output "specialized_parser_cloud_run_job_name" {
  description = "Cloud Run specialized parser job name"
  value       = google_cloud_run_v2_job.specialized_parser_processor_job.name
}

output "specialized_parser_service_account" {
  description = "Specialized Parser service account"
  value       = module.specialized_parser_account.email
}

output "specialized_processors_ids_json" {
  description = "JSON encoded string of all supported labels as keys and the corresponding processor id for each as values."
  value = jsonencode({
    "invoice" = google_document_ai_processor.eks-invoice-processor.id
    "form"    = google_document_ai_processor.eks-form-processor.id
  })
}

output "specialized_parser_db_user" {
  description = "The AlloyDB db role associated with the service account identity of the specializer parser Cloud Run job"
  value       = google_alloydb_user.specialized_parser_user.user_id
}

output "db_role_content_hash" {
  description = "Additional deployment trigger to force rerun module.gcloud_build_job_to_configure_alloydb_schema if terraform reverts the db roles on specialized_parser_role (flaky)"
  value       = sha512(terraform_data.dbrole_deployment_trigger.id)
}

output "processed_documents_bq_table_name" {
  description = "The BigQuery table that holds the extracted entities from the processed_documents"
  value = google_bigquery_table.processed_documents.table_id
}

output "processed_documents_bq_table_project_id" {
  description = "The BigQuery table project that holds the extracted entities from the processed_documents"
  value = google_bigquery_table.processed_documents.project
}

output "processed_documents_bq_table_dataset" {
  description = "The BigQuery table dataset that holds the extracted entities from the processed_documents"
  value = google_bigquery_table.processed_documents.dataset_id
}
