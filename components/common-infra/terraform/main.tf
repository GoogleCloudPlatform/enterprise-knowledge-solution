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

locals {
  dpu_label = {
    goog-packaged-solution : "eks-solution"
  }
}
module "project_services" {
  source                      = "github.com/terraform-google-modules/terraform-google-project-factory.git//modules/project_services?ref=ff00ab5032e7f520eb3961f133966c6ced4fd5ee" # commit hash of version 17.0.0
  project_id                  = var.project_id
  disable_services_on_destroy = false
  disable_dependent_services  = false
  activate_apis = [
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "bigquery.googleapis.com",
    "alloydb.googleapis.com",
    "servicenetworking.googleapis.com",
  ]
}

resource "google_artifact_registry_repository" "docker-repo" {
  project       = module.project_services.project_id
  format        = "DOCKER"
  location      = var.region
  repository_id = "dpu-docker-repo"
  description   = "Docker containers"
  labels        = local.dpu_label
}

module "cloud_build_account" {
  source     = "github.com/terraform-google-modules/terraform-google-service-accounts?ref=a11d4127eab9b51ec9c9afdaf51b902cd2c240d9" #commit hash of version 4.0.0
  project_id = var.project_id
  names      = ["cloud-build"]
  project_roles = [
    "${var.project_id}=>roles/logging.logWriter",
    "${var.project_id}=>roles/storage.objectViewer",
    "${var.project_id}=>roles/artifactregistry.writer",
    "${var.project_id}=>roles/run.developer",
    "${var.project_id}=>roles/iam.serviceAccountUser",
  ]
  display_name = "Cloud Build Service Account"
  description  = "specific custom service account for Cloud Build"
}


# Propagation time for change of access policy typically takes 2 minutes
# according to https://cloud.google.com/iam/docs/access-change-propagation
# this wait make sure the policy changes are propagated before proceeding
# with the build
resource "time_sleep" "wait_for_policy_propagation" {
  create_duration = "120s"
  depends_on = [
    module.cloud_build_account
  ]
}
