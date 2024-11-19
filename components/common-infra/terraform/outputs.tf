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
output "artifact_repo" {
  description = "Cloud arctifact repository object"
  value       = google_artifact_registry_repository.docker-repo
}

output "cloud_build_service_account" {
  description = "IAM service account to run builds on top of Cloud Build"
  value       = module.cloud_build_account
}

output "project_id" {
  description = "Google Cloud project user by the module."
  value       = module.project_services.project_id
}

output "gcs_input_bucket_name" {
  description = "Cloud Storage bucket for input files"
  value       = module.input_bucket.name
}

output "gcs_process_bucket_name" {
  description = "Cloud Storage bucket for processing of files"
  value       = module.process_bucket.name
}

output "gcs_reject_bucket_name" {
  description = "Cloud Storage bucket for storing documents that were not able to be processed"
  value       = module.reject_bucket.name
}

output "bq_store_dataset_id" {
  description = "BigQuery data store dataset"
  value       = module.docs_store_dataset.bigquery_dataset.dataset_id
}

output "vpc_network_id" {
  value = local.vpc_network_id
}

output "vpc_network_name" {
  value = local.vpc_network_name
}

output "alloydb_cluster_name" {
  value = module.docs_results.cluster_name
}

output "alloydb_primary_instance" {
  value = module.docs_results.primary_instance_id
}

output "alloydb_location" {
  value = var.region
}

output "alloydb_cluster_ready" {
  description = "creating the alloydb resource in terraform does not guarantee it's in the ready state, so subsequent steps fail. This resource exists to force a sleep_timer that is referencable from other modules "
  value       = true
  depends_on  = [time_sleep.wait_for_alloydb_ready_state]
}

output "serverless_connector_subnet" {
  description = "the subnet used by Cloud Run for private access to alloydb"
  value       = google_compute_subnetwork.serverless_connector_subnet.name
}

output "specialized_parser_cloud_run_job_name" {
  description = "Specialized Parser job name"
  value       = var.specialized_parser_cloud_run_job_name
}
