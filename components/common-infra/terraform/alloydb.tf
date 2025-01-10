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
      "alloydb.iam_authentication"  = "true",
      "alloydb.enable_pgaudit"      = "on",
      "password.enforce_complexity" = "on"
    }
  }

  #depends_on = [google_service_networking_connection.default]
}

resource "time_sleep" "wait_for_alloydb_ready_state" {
  create_duration = "600s"
  depends_on = [
    module.docs_results
  ]
}
