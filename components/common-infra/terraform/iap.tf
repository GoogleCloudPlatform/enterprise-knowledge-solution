# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

/*
 * IAP Configuration
 */



# OAuth Client
resource "google_iap_client" "project_client" {
  display_name = "Enterprise Knowledge ADP client"
  brand        = "projects/${data.google_project.project.number}/brands/${data.google_project.project.number}"
}

resource "google_project_service_identity" "iap_sa" {
  provider = google-beta
  project  = module.project_services.project_id
  service  = "iap.googleapis.com"
}
