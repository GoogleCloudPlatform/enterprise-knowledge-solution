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
  env_name                      = "dpu-composer"
  cluster_secondary_range_name  = "composer-subnet-cluster"
  services_secondary_range_name = "composer-subnet-services"
  composer_sa_roles             = [for role in var.composer_sa_roles : "${module.project_services.project_id}=>${role}"]
  dpu_label = {
    goog-packaged-solution : "eks-solution"
  }
}

module "project_services" {
  source                      = "terraform-google-modules/project-factory/google//modules/project_services"
  version                     = "14.5.0"
  project_id                  = var.project_id
  disable_services_on_destroy = false
  disable_dependent_services  = false
  activate_apis               = var.required_apis
  activate_api_identities = [{
    "api" : "composer.googleapis.com",
    "roles" : [
      "roles/composer.ServiceAgentV2Ext",
      "roles/composer.serviceAgent",
    ]
  }]
}

module "composer_service_account" {
  source  = "terraform-google-modules/service-accounts/google"
  version = "~> 4.2"

  project_id = module.project_services.project_id
  prefix     = local.env_name
  names = [
    "runner"
  ]
  project_roles = local.composer_sa_roles
}

module "vpc" {
  source  = "terraform-google-modules/network/google//modules/subnets"
  version = "~> 9.1"

  project_id   = module.project_services.project_id
  network_name = var.vpc_network_name

  subnets = [{
    subnet_name           = "composer-subnet"
    subnet_ip             = "10.10.10.0/24"
    subnet_region         = var.region
    subnet_private_access = "true"
  }]

  secondary_ranges = {
    composer-subnet = [
      {
        range_name    = local.cluster_secondary_range_name
        ip_cidr_range = "10.154.0.0/17"
      },
      {
        range_name    = local.services_secondary_range_name
        ip_cidr_range = "10.154.128.0/22"
      },
    ]
  }
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


resource "google_composer_environment" "composer_env" {
  project = module.project_services.project_id
  name    = local.env_name
  region  = var.region
  labels  = local.dpu_label

  config {
    private_environment_config {
      connection_type         = var.enable_private_ip ? "PRIVATE_SERVICE_CONNECT" : null
      enable_private_endpoint = var.enable_private_ip
    }
    software_config {
      image_version = var.composer_version
      env_variables = var.composer_env_variables
      pypi_packages = var.composer_additional_pypi_packages
    }
    environment_size = var.composer_environment_size
    node_config {
      network         = var.vpc_network_id
      subnetwork      = module.vpc.subnets["${var.region}/composer-subnet"].id
      service_account = module.composer_service_account.email
      ip_allocation_policy {
        cluster_secondary_range_name  = local.cluster_secondary_range_name
        services_secondary_range_name = local.services_secondary_range_name
      }
    }
  }

  depends_on = [
    google_project_iam_member.gce_gcs_access,
    google_project_iam_member.gce_ar_access
  ]
}

resource "google_storage_bucket_object" "workflow_orchestrator_dag" {
  for_each       = fileset("${path.module}/../src", "**/*.py")
  name           = "dags/${each.value}"
  bucket         = google_composer_environment.composer_env.storage_config.0.bucket
  source         = "${path.module}/../src/${each.value}"
  detect_md5hash = "true"
}
