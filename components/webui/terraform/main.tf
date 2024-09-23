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

/*
 * Activate required service API:s
 */
module "project_services" {
  source                      = "github.com/terraform-google-modules/terraform-google-project-factory.git//modules/project_services?ref=ff00ab5032e7f520eb3961f133966c6ced4fd5ee" # commit hash of version 17.0.0
  project_id                  = var.project_id
  disable_services_on_destroy = false
  disable_dependent_services  = false
  activate_apis = [
    "compute.googleapis.com",
    "iap.googleapis.com",
    "aiplatform.googleapis.com"
  ]
}

data "google_project" "project" {
  project_id = module.project_services.project_id
}

/*
 * IAP Configuration
 */

# OAuth Client
resource "google_iap_client" "project_client" {
  display_name = "Enterprise Knowledge Search client"
  brand        = "projects/${data.google_project.project.number}/brands/${data.google_project.project.number}"
}

resource "google_project_iam_member" "iap_users" {
  for_each = toset(var.iap_access_domains)
  project  = module.project_services.project_id
  role     = "roles/iap.httpsResourceAccessor"
  member   = each.key
}

data "google_compute_default_service_account" "default" {
  project = module.project_services.project_id
}

# Grant default compute engine view access to cloud storage
resource "google_project_iam_member" "gce_gcs_access" {
  project = module.project_services.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${data.google_compute_default_service_account.default.email}"
}
# Grant default compute engine view access to artifact registry
resource "google_project_iam_member" "gce_ar_access" {
  project = module.project_services.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${data.google_compute_default_service_account.default.email}"
}

# Propagation time for change of access policy typically takes 2 minutes
# according to https://cloud.google.com/iam/docs/access-change-propagation
# this wait make sure the policy changes are propagated before proceeding
# with the build
resource "time_sleep" "wait_for_policy_propagation" {
  create_duration = "120s"
  depends_on = [
    google_project_iam_member.gce_gcs_access,
    google_project_iam_member.gce_ar_access
  ]
}
