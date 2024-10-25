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
  eks_label = {
    goog-packaged-solution : "eks-solution"
  }
  service_account_name = var.doc_registry_service_cloud_run_job_name
}

# Enable APIs
# See github.com/terraform-google-modules/terraform-google-project-factory
# The modules/project_services
module "project_services" {
  source                      = "github.com/terraform-google-modules/terraform-google-project-factory.git//modules/project_services?ref=ff00ab5032e7f520eb3961f133966c6ced4fd5ee" # commit hash of version 17.0.0
  project_id                  = var.project_id
  disable_services_on_destroy = false
  disable_dependent_services  = false
  activate_apis = [
    # General container build and registry
    "bigquery.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "run.googleapis.com",
    "compute.googleapis.com",
    "containerscanning.googleapis.com"
  ]

  # Provide more access to the cloudbuild service account
  activate_api_identities = [{
    "api" : "cloudbuild.googleapis.com",
    "roles" : [
      "roles/run.admin",
      # Required for Cloud Run to launch as the normal compute service account
      "roles/iam.serviceAccountUser",
    ]
    },
    {
      "api" : "pubsub.googleapis.com",
      # PubSub publish to Cloud Run
      "roles" : [
        "roles/iam.serviceAccountTokenCreator",
      ],
    }
  ]
}

module "doc_registry_service_account" {
  source     = "github.com/terraform-google-modules/terraform-google-service-accounts?ref=a11d4127eab9b51ec9c9afdaf51b902cd2c240d9" #commit hash of version 4.0.0
  project_id = var.project_id
  prefix     = "eks"
  names      = [local.service_account_name]
  project_roles = [
    "${var.project_id}=>roles/storage.objectUser",
    "${var.project_id}=>roles/bigquery.dataEditor",
    "${var.project_id}=>roles/bigquery.jobUser"
  ]
  display_name = "Document Registry Service Account"
  description  = "Account used to run the document registry service jobs"
}

resource "google_cloud_run_v2_job" "doc-registry-service-job" {
  name     = var.doc_registry_service_cloud_run_job_name
  location = var.region

  template {
    template {
      service_account = module.doc_registry_service_account.email
      containers {
        image = local.image_name_and_tag
      }
    }
  }
  depends_on = [
    module.gcloud.wait
  ]
}