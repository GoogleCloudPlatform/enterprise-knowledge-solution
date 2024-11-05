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

  cluster_id           = var.alloy_db_cluster_id
  cluster_location     = var.region
  cluster_labels       = {}
  cluster_display_name = var.alloy_db_cluster_id
  psc_enabled          = true
  # network_self_link    = replace(module.vpc.network_self_link, "https://www.googleapis.com/compute/v1/", "")

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
}
