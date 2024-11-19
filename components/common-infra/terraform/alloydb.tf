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
  # specification of the alloy db docs of removing the .gserviceaccount.com part: https://cloud.google.com/alloydb/docs/manage-iam-authn#create-user
  alloydb_username     = replace(module.configure_schema_account.email, ".gserviceaccount.com", "")
  service_account_name = var.configure_schema_cloud_run_job_name
}

resource "google_vpc_access_connector" "vpc_connector" {
  project       = module.project_services.project_id
  name          = "alloy-db-vpc-connector"
  region        = var.region
  network       = local.vpc_network_id
  ip_cidr_range = "10.8.0.0/28"
  min_instances = 2
  max_instances = 3
}

resource "google_compute_subnetwork" "serverless_connector_subnet" {
  name                     = var.serverless_connector_subnet
  ip_cidr_range            = var.serverless_connector_subnet_range
  region                   = var.region
  network                  = local.vpc_network_name
  private_ip_google_access = true
  log_config {
    aggregation_interval = "INTERVAL_10_MIN"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}

resource "google_compute_global_address" "private_ip_address" {
  name          = "private-ip-address"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = local.vpc_network_id
}

resource "google_service_networking_connection" "default" {
  network                 = local.vpc_network_id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
}

resource "google_compute_network_peering_routes_config" "peering_routes" {
  peering = google_service_networking_connection.default.peering
  network = local.vpc_network_name

  import_custom_routes = true
  export_custom_routes = true
}

module "docs_results" {
  source = "github.com/GoogleCloudPlatform/terraform-google-alloy-db?ref=fa1d5faf54b56abfe410f5c29483e365d48ec1a3" #commit hash for version 3.2.0

  project_id = module.project_services.project_id

  cluster_id        = var.alloy_db_cluster_id
  cluster_location  = var.region
  cluster_labels    = {}
  psc_enabled       = false
  network_self_link = replace(local.vpc_network_self_link, "https://www.googleapis.com/compute/v1/", "")


  primary_instance = {
    instance_id       = "${var.alloy_db_cluster_id}-primary"
    instance_type     = "PRIMARY"
    machine_cpu_count = 2
    database_flags = {
      # This flag enables authenticating using IAM, however, creating databases and tables from terraform is not
      # currently supported. This goes for managing users permissions over databases and tables as well.
      # This means we will use throughout the example only the `public` built in database, which can be accessed by any
      # authenticated user.
      "alloydb.iam_authentication" = "true"
    }
  }

  depends_on = [google_service_networking_connection.default]
}

module "configure_schema_account" {
  source     = "github.com/terraform-google-modules/terraform-google-service-accounts?ref=a11d4127eab9b51ec9c9afdaf51b902cd2c240d9" #commit hash of version 4.0.0
  project_id = var.project_id
  prefix     = "eks"
  names      = [local.service_account_name]
  project_roles = [
    "${var.project_id}=>roles/documentai.apiUser",
    "${var.project_id}=>roles/alloydb.databaseUser",
    "${var.project_id}=>roles/alloydb.client",
    "${var.project_id}=>roles/serviceusage.serviceUsageConsumer",
    "${var.project_id}=>roles/documentai.editor",
    "${var.project_id}=>roles/bigquery.dataEditor",
    "${var.project_id}=>roles/bigquery.jobUser",
    "${var.project_id}=>roles/storage.admin",
  ]
  display_name = "AlloyDB db configuration Account"
  description  = "Account used to run configure the schema and db roles in AlloyDB"
}

resource "google_alloydb_user" "schema_setup_user" {
  cluster        = module.docs_results.cluster_name
  user_id        = local.alloydb_username
  user_type      = "ALLOYDB_IAM_USER"
  database_roles = ["alloydbiamuser", "alloydbsuperuser"]

  depends_on = [time_sleep.wait_for_alloydb_ready_state]
}

resource "google_cloud_run_v2_job" "configure_schema_processor_job" {
  name     = var.configure_schema_cloud_run_job_name
  location = var.region
  template {
    template {
      service_account = module.configure_schema_account.email
      vpc_access {
        network_interfaces {
          network    = local.vpc_network_name
          subnetwork = google_compute_subnetwork.serverless_connector_subnet.name
        }
        egress = "PRIVATE_RANGES_ONLY"
      }
      containers {
        image = local.image_name_and_tag
        name  = var.configure_schema_cloud_run_job_name
        resources {
          limits = {
            cpu    = "2"
            memory = "2048Mi"
          }
        }
        env {
          name  = "ALLOYDB_INSTANCE"
          value = module.docs_results.primary_instance_id
        }
        env {
          name  = "ALLOYDB_DATABASE"
          value = var.alloydb_database
        }
        env {
          name  = "ALLOYDB_USER"
          value = replace(module.configure_schema_account.email, ".gserviceaccount.com", "")
        }
      }
    }
  }
  lifecycle {
    ignore_changes = [
      effective_labels["goog-packaged-solution"],
      terraform_labels["goog-packaged-solution"],
      labels["goog-packaged-solution"]
    ]
  }
}

resource "time_sleep" "wait_for_alloydb_ready_state" {
  create_duration = "600s"
  depends_on = [
    module.docs_results
  ]
}
