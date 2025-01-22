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
  alloydb_username     = replace(module.doc_deletion_account.email, ".gserviceaccount.com", "")
  service_account_name = var.doc_deletion_cloud_run_job_name
}

resource "google_cloud_run_v2_job" "doc_deletion_job" {
  name     = var.doc_deletion_cloud_run_job_name
  location = var.region
  template {
    template {
      service_account = module.doc_deletion_account.email
      vpc_access {
        network_interfaces {
          network    = var.vpc_network_name
          subnetwork = var.serverless_connector_subnet
        }
        egress = "ALL_TRAFFIC"
      }
      containers {
        image = local.image_name_and_tag
        name  = var.doc_deletion_cloud_run_job_name
        resources {
          limits = {
            cpu    = "2"
            memory = "2048Mi"
          }
        }
        env {
          name  = "ALLOYDB_INSTANCE"
          value = var.alloydb_primary_instance
        }
        env {
          name  = "ALLOYDB_DATABASE"
          value = var.alloydb_database
        }
        env {
          name  = "ALLOYDB_USER_CONFIG"
          value = local.alloydb_username
        }
        env {
          name  = "DATA_STORE_PROJECT_ID"
          value = var.data_store_project_id
        }
        env {
          name  = "DATA_STORE_REGION"
          value = var.data_store_region
        }
        env {
          name  = "DATA_STORE_COLLECTION"
          value = var.data_store_collection
        }
        env {
          name  = "DATA_STORE_ID"
          value = var.data_store_id
        }
        env {
          name  = "DATA_STORE_BRANCH"
          value = var.data_store_branch
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
  deletion_protection = false
}

module "doc_deletion_account" {
  source     = "github.com/terraform-google-modules/terraform-google-service-accounts?ref=a11d4127eab9b51ec9c9afdaf51b902cd2c240d9" #commit hash of version 4.0.0
  project_id = var.project_id
  prefix     = "eks"
  names      = [local.service_account_name]
  project_roles = [
    "${var.project_id}=>roles/alloydb.databaseUser",
    "${var.project_id}=>roles/alloydb.client",
    "${var.project_id}=>roles/serviceusage.serviceUsageConsumer",
    "${var.project_id}=>roles/bigquery.dataEditor",
    "${var.project_id}=>roles/bigquery.jobUser",
    "${var.project_id}=>roles/storage.admin",
    "${var.project_id}=>roles/discoveryengine.editor",
  ]
  display_name = "Doc Deletion Job Account"
  description  = "Account used to run doc deletion in Agent Builder, BigQuery, AlloyDB and other storage services"
}

resource "terraform_data" "dbrole_deployment_trigger" {
  # workaround to explicitly retrigger module.gcloud_build_job_to_configure_alloydb_schema if terraform reverts the db roles on specialized_parser_role (flaky)
  input            = google_alloydb_user.doc_deletion_db_user
  triggers_replace = google_alloydb_user.doc_deletion_db_user.database_roles
}


resource "google_alloydb_user" "doc_deletion_db_user" {
  cluster        = var.alloy_db_cluster_id
  user_id        = local.alloydb_username
  user_type      = "ALLOYDB_IAM_USER"
  database_roles = ["alloydbiamuser"]

  depends_on = [var.alloydb_cluster_ready]
  lifecycle {
    ignore_changes = [database_roles]
  }
}
