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


resource "google_compute_global_address" "private_ip_alloc" {
  project       = var.project_id
  name          = "adb-psa"
  address_type  = "INTERNAL"
  purpose       = "VPC_PEERING"
  prefix_length = 12
  network       = module.vpc.network_id
  address       = "172.16.0.0"
}

resource "google_service_networking_connection" "vpc_connection" {
  network                 = module.vpc.network_id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_alloc.name]
  deletion_policy         = "ABANDON"
}

module "docs_results" {
  source         = "GoogleCloudPlatform/alloy-db/google"
  version        = "~> 3.0"

  project_id     = module.project_services.project_id

  cluster_id           = var.alloy_db_cluster_id
  cluster_location     = var.region
  cluster_labels       = {}
  cluster_display_name = var.alloy_db_cluster_id
#   cluster_initial_user = {
#     user     = var.alloy_db_username
#     password = var.alloy_db_password
#   }
  network_self_link = module.vpc.network_id

  primary_instance = {
    instance_id = "${var.alloy_db_cluster_id}-primary"
    instance_type = "PRIMARY",
    machine_cpu_count = 2
  }
#   read_pool_instance = null
  depends_on = [
    google_service_networking_connection.vpc_connection
  ]
}
