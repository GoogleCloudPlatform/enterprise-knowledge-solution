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
    "appengine.googleapis.com",
    "compute.googleapis.com",
    "appengineflex.googleapis.com",
    "iap.googleapis.com",
    "aiplatform.googleapis.com"
  ]
}

/*
 * VPC configuration for App Engine
 */

module "webui-subnet" {
  source       = "github.com/terraform-google-modules/terraform-google-network.git//modules/subnets?ref=2477e469c9734638c9ed83e69fe8822452dacbc6" #commit hash of version 9.2.0
  project_id   = module.project_services.project_id
  network_name = var.vpc_network_name

  subnets = [{
    subnet_name   = "dpu-ui-subnet"
    subnet_ip     = "10.10.20.0/24"
    subnet_region = var.region
  }]
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

/*
 * Configuring of App Engine Flex and permission
 */

# Configure App Engine region
resource "google_app_engine_application" "app" {
  project     = module.project_services.project_id
  location_id = var.region

  iap {
    oauth2_client_id     = google_iap_client.project_client.client_id
    oauth2_client_secret = google_iap_client.project_client.secret
    enabled              = true
  }

  lifecycle {
    ignore_changes = [
      serving_status,
      location_id
    ]
  }
}

# Identify the app engine service account
data "google_app_engine_default_service_account" "default" {
  project = module.project_services.project_id
  depends_on = [
    google_app_engine_application.app
  ]
}

resource "google_artifact_registry_repository_iam_binding" "registry_viewer" {
  project    = var.project_id
  location   = var.region
  repository = var.artifact_repo
  role       = "roles/artifactregistry.reader"
  members = [
    "serviceAccount:${data.google_app_engine_default_service_account.default.email}"
  ]
}

# Grant project access to use the network
resource "google_project_iam_member" "gae_api" {
  project = module.project_services.project_id
  role    = "roles/compute.networkUser"
  member  = "serviceAccount:${data.google_app_engine_default_service_account.default.email}"
}

# Grant project access to write to logs
resource "google_project_iam_member" "logs_writer" {
  project = module.project_services.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${data.google_app_engine_default_service_account.default.email}"
}

# Grant access to Vertex AI
resource "google_project_iam_member" "vertex_ai_user" {
  project = module.project_services.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${data.google_app_engine_default_service_account.default.email}"
}

# Grant access to Agent Builder
resource "google_project_iam_member" "agent_builder_viewer" {
  project = module.project_services.project_id
  role    = "roles/discoveryengine.viewer"
  member  = "serviceAccount:${data.google_app_engine_default_service_account.default.email}"
}

# Grant access to Object Storage
resource "google_project_iam_member" "gcs_object_store" {
  project = module.project_services.project_id
  role    = "roles/storage.objectUser"
  member  = "serviceAccount:${data.google_app_engine_default_service_account.default.email}"
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

/*
 * Configure IAP for App Engine
 */

# Policy for users who can access App Engine
data "google_iam_policy" "end_users" {
  binding {
    role    = "roles/iap.httpsResourceAccessor"
    members = var.iap_access_domains
  }
}

locals {
  ui_service_name     = "dpu-ui"
  cloud_build_fileset = setunion(fileset(path.module, "../src/**"), fileset(path.module, "../Dockerfile"), fileset(path.module, "../requirements.txt"))
  cloud_build_content_hash = sha512(join(",", [
  for f in local.cloud_build_fileset : fileexists("${path.module}/${f}") ? filesha512("${path.module}/${f}") : sha512("file-not-found")]))
}

# Build and upload the app container
module "app_build" {
  source = "github.com/terraform-google-modules/terraform-google-gcloud?ref=db25ab9c0e9f2034e45b0034f8edb473dde3e4ff" # commit hash of version 3.5.0

  platform        = "linux"
  create_cmd_body = "builds submit --region ${var.region} --project ${var.project_id} --tag \"${var.region}-docker.pkg.dev/${module.project_services.project_id}/${var.artifact_repo}/${local.ui_service_name}\" \"${path.module}/../\""
  enabled         = true

  create_cmd_triggers = {
    source_contents_hash = local.cloud_build_content_hash
  }

  module_depends_on = [
    time_sleep.wait_for_policy_propagation
  ]
}

# Apply policy to IAP for App Engine
resource "google_iap_web_type_app_engine_iam_policy" "policy" {
  project     = google_app_engine_application.app.project
  app_id      = google_app_engine_application.app.app_id
  policy_data = data.google_iam_policy.end_users.policy_data
}

resource "null_resource" "appengine_deploy_trigger" {
  triggers = {
    source_contents_hash = local.cloud_build_content_hash
  }
}

resource "google_app_engine_flexible_app_version" "deployed_version" {
  # version_id = "v${local.cloud_build_content_hash}"
  version_id = "v1"
  # version_id = "v${formatdate("YYYYMMDDHHMMSS", timestamp())}"
  project = module.project_services.project_id
  service = var.app_engine_service_name
  runtime = "custom"

  deployment {
    container {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_repo}/${local.ui_service_name}:latest"
    }
  }

  liveness_check {
    path              = "/healthz"
    check_interval    = "31s"
    timeout           = "4s"
    failure_threshold = "2"
    success_threshold = "2"
  }

  readiness_check {
    path              = "/healthz"
    check_interval    = "30s"
    timeout           = "4s"
    failure_threshold = "2"
    success_threshold = "2"
    app_start_timeout = "120s"
  }

  network {
    name       = var.vpc_network_id
    subnetwork = module.webui-subnet.subnets["${var.region}/dpu-ui-subnet"].name
    # forwarded_ports = ["${local.forwarded_port}"]
  }

  resources {
    cpu       = "2"
    memory_gb = "4"
    disk_gb   = "40"
  }

  automatic_scaling {
    min_total_instances = "1"
    max_total_instances = "2"
    cpu_utilization {
      target_utilization = "0.5"
    }
  }

  env_variables = {
    PROJECT_ID                  = module.project_services.project_id
    AGENT_BUILDER_LOCATION      = var.vertex_ai_data_store_region
    AGENT_BUILDER_DATA_STORE_ID = var.agent_builder_data_store_id
    AGENT_BUILDER_SEARCH_ID     = var.agent_builder_search_id
  }

  # Depend on permissions being defined
  depends_on = [
    google_artifact_registry_repository_iam_binding.registry_viewer,
    google_project_iam_member.gae_api,
    google_project_iam_member.logs_writer,
    module.app_build.wait
  ]

  # Ignore serving status for this version
  noop_on_destroy = true
  lifecycle {
    ignore_changes = [
      serving_status,
      deployment[0].container[0].image
    ]
  }
}
