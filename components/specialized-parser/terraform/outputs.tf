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
