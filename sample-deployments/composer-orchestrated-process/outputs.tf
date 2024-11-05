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

output "gcs_input_bucket_name" {
  description = "GCS input bucket name"
  value       = module.common_infra.gcs_input_bucket_name
}

output "gcs_process_bucket_name" {
  description = "GCS processing bucket name"
  value       = module.common_infra.gcs_process_bucket_name
}

output "gcs_reject_bucket_name" {
  description = "GCS reject bucket name"
  value       = module.common_infra.gcs_reject_bucket_name
}

output "composer_uri" {
  description = "Cloud Composer Airflow URI"
  value       = module.dpu_workflow.composer_uri
}

output "agent_app_uri" {
  description = "Agent Builder Search App URI"
  value       = "https://console.cloud.google.com/gen-app-builder/locations/${var.vertex_ai_data_store_region}/engines/${google_discovery_engine_search_engine.basic.engine_id}/preview/search?project=${var.project_id}"
}

output "webui_dns_config" {
  description = "DNS Record for WebUI"
  value       = module.dpu_ui.dns_configuration
}

output "classifier_processor_id" {
  description = "The DocAI Custom Classifier processor id"
  value = var.custom_classifier_id
}

output "specialized_processors_ids_json" {
  description = "JSON encoded string of all supported labels as keys and the corresponding processor id for each as values."
  value = jsondecode(module.specialized_parser_job.specialized_processors_ids_json)
}

output "composer_location" {
  description = "Location of Cloud Composer"
  value = module.dpu_workflow.composer_location
}
