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
  source                      = "terraform-google-modules/project-factory/google//modules/project_services"
  version                     = "14.5.0"
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

locals {
  ui_service_name     = "dpu-ui"
  cloud_build_fileset = setunion(fileset("${path.module}", "../src/**"), fileset("${path.module}", "../Dockerfile"), fileset("${path.module}", "../requirements.txt"))
  cloud_build_content_hash = sha512(join(",", [
  for f in local.cloud_build_fileset : fileexists("${path.module}/${f}") ? filesha512("${path.module}/${f}") : sha512("file-not-found")]))
}

# Build and upload the app container
module "app_build" {
  source  = "terraform-google-modules/gcloud/google"
  version = "~> 3.4"

  platform        = "linux"
  create_cmd_body = "builds submit --region ${var.region} --project ${var.project_id} --tag \"${var.region}-docker.pkg.dev/${module.project_services.project_id}/${var.artifact_repo.name}/${local.ui_service_name}\" \"${path.module}/../\""
  enabled         = true

  create_cmd_triggers = {
    source_contents_hash = local.cloud_build_content_hash
  }

  module_depends_on = [
    time_sleep.wait_for_policy_propagation
  ]
}
