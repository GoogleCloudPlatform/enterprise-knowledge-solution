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
  source                      = "github.com/terraform-google-modules/terraform-google-project-factory.git//modules/project_services?ref=ff00ab5032e7f520eb3961f133966c6ced4fd5ee" # commit hash of version 17.0.0
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
  source = "github.com/terraform-google-modules/terraform-google-service-accounts?ref=a11d4127eab9b51ec9c9afdaf51b902cd2c240d9" #commit hash of version 4.0.0

  project_id = module.project_services.project_id
  prefix     = local.env_name
  names = [
    "runner"
  ]
  project_roles = local.composer_sa_roles
}

module "dpu-subnet" {
  source = "github.com/terraform-google-modules/terraform-google-network.git//modules/subnets?ref=2477e469c9734638c9ed83e69fe8822452dacbc6" #commit hash of version 9.2.0

  project_id   = module.project_services.project_id
  network_name = var.vpc_network_name

  subnets = [{
    subnet_name           = "composer-subnet"
    subnet_ip             = var.composer_cidr.subnet_primary
    subnet_region         = var.region
    subnet_private_access = "true"
    subnet_flow_logs      = "true"
  }]

  secondary_ranges = {
    composer-subnet = [
      {
        range_name    = local.cluster_secondary_range_name
        ip_cidr_range = var.composer_cidr.cluster_secondary_range
      },
      {
        range_name    = local.services_secondary_range_name
        ip_cidr_range = var.composer_cidr.services_secondary_range
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
      subnetwork      = module.dpu-subnet.subnets["${var.region}/composer-subnet"].id
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
  bucket         = google_composer_environment.composer_env.storage_config[0].bucket
  source         = "${path.module}/../src/${each.value}"
  detect_md5hash = "true"
}
