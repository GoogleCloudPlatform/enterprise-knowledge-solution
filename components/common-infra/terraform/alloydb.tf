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

data "google_project" "eks_project" {
  project_id = var.project_id
}

module "docs_results" {
  source = "github.com/GoogleCloudPlatform/terraform-google-alloy-db?ref=eda758770239cd3dd1122834ef0c0429659a0234" #commit hash for version 3.2.1

  project_id = module.project_services.project_id

  cluster_id                    = var.alloy_db_cluster_id
  cluster_location              = var.region
  cluster_labels                = {}
  psc_enabled                   = true
  network_self_link             = null
  psc_allowed_consumer_projects = [data.google_project.eks_project.number]


  primary_instance = {
    instance_id       = "${var.alloy_db_cluster_id}-primary"
    instance_type     = "PRIMARY"
    machine_cpu_count = 2
    database_flags = {
      "alloydb.iam_authentication"  = "true",
      "alloydb.enable_pgaudit"      = "on",
      "password.enforce_complexity" = "on"
    }
  }
}

resource "google_compute_address" "alloydb_psc_endpoint" {
  region       = var.region
  name         = var.alloydb_psc_endpoint
  subnetwork   = google_compute_subnetwork.serverless_connector_subnet.id
  address_type = "INTERNAL"
}

resource "google_compute_forwarding_rule" "alloydb_psc_fwd_rule" {
  region                  = var.region
  name                    = var.alloydb_psc_fwd_rule
  target                  = module.docs_results.primary_psc_attachment_link
  load_balancing_scheme   = "" # need to override EXTERNAL default when target is a service attachment
  network                 = local.vpc_network_id
  ip_address              = google_compute_address.alloydb_psc_endpoint.id
  allow_psc_global_access = true
}
resource "google_dns_managed_zone" "alloydb_dns" {
  name        = var.alloydb_dns
  dns_name    = module.docs_results.primary_psc_dns_name
  description = "DNS Zone for EKS AlloyDB instance"
  visibility  = "private"
  private_visibility_config {
    networks {
      network_url = local.vpc_network_id
    }
  }
}
resource "google_dns_record_set" "alloy_psc" {
  name         = module.docs_results.primary_psc_dns_name
  type         = "A"
  ttl          = 300
  managed_zone = google_dns_managed_zone.alloydb_dns.name
  rrdatas      = [google_compute_address.alloydb_psc_endpoint.address]
}

resource "time_sleep" "wait_for_alloydb_ready_state" {
  create_duration = "600s"
  depends_on = [
    module.docs_results
  ]
}
