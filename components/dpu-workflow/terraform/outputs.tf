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

output "composer_dag_gcs_bucket" {
  description = "Stores the DAGs for the Cloud Composer environment."
  value       = google_composer_environment.composer_env.storage_config[0].bucket
}

output "composer_uri" {
  description = "Cloud Composer Airflow URI"
  value       = google_composer_environment.composer_env.config[0].airflow_uri
}

output "composer_location" {
  description = "Cloud Composer Location"
  value       = google_composer_environment.composer_env.region
}

