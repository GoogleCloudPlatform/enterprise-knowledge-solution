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

# Enable APIs
# See github.com/terraform-google-modules/terraform-google-project-factory
# The modules/project_services
locals {
  alloydb_username = replace(module.specialized_parser_account.email, ".gserviceaccount.com", "")
  alloydb_cluster_name_split = split("/", var.alloydb_cluster)
  alloydb_cluster_name = element(local.alloydb_cluster_name_split, length(local.alloydb_cluster_name_split) - 1)
}

module "project_services" {
  source                      = "github.com/terraform-google-modules/terraform-google-project-factory.git//modules/project_services?ref=ff00ab5032e7f520eb3961f133966c6ced4fd5ee" # commit hash of version 17.0.0
  project_id                  = var.project_id
  disable_services_on_destroy = false
  disable_dependent_services  = false
  activate_apis = [
    # General container build and registry
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "documentai.googleapis.com",
    "run.googleapis.com",
    "compute.googleapis.com",
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
        #"roles/iam.serviceAccountUser",
        "roles/iam.serviceAccountTokenCreator",
      ],
    }
  ]
}

module "specialized_parser_account" {
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
  display_name = "Specialized Parser Account"
  description  = "Account used to run the specialized parser jobs"
}

resource "google_alloydb_user" "specialized_parser_user" {
  cluster = var.alloydb_cluster
  # specification of the alloy db docs of removing the .gserviceaccount.com part: https://cloud.google.com/alloydb/docs/manage-iam-authn#create-user
  user_id        = local.alloydb_username
  user_type      = "ALLOYDB_IAM_USER"
  database_roles = ["alloydbsuperuser", "alloydbiamuser"]
}

# See github.com/terraform-google-modules/terraform-google-gcloud
module "set_superuser" {
  source                = "github.com/terraform-google-modules/terraform-google-gcloud?ref=db25ab9c0e9f2034e45b0034f8edb473dde3e4ff" # commit hash of version 3.5.0
  create_cmd_entrypoint = "gcloud"
  create_cmd_body       = <<-EOT
    alloydb users set-superuser ${local.alloydb_username} \
      --cluster=${local.alloydb_cluster_name} \
      --superuser=true \
      --project=${var.project_id} \
      --region=${var.region}
  EOT
  enabled               = true

  module_depends_on = [google_alloydb_user.specialized_parser_user]

  skip_download = true

}


resource "google_cloud_run_v2_job" "specialized_parser_processor_job" {
  name     = var.specialized_parser_cloud_run_job_name
  location = var.region
  lifecycle {
    ignore_changes = [terraform_labels, effective_labels]
  }
  template {
    template {
      service_account = module.specialized_parser_account.email
      vpc_access {
        network_interfaces {
          network    = var.network
          subnetwork = var.subnet
        }
        egress = "PRIVATE_RANGES_ONLY"
      }
      containers {
        image = local.image_name_and_tag
        name  = var.specialized_parser_cloud_run_job_name
        resources {
          limits = {
            cpu    = "2"
            memory = "2048Mi"
          }
        }
        # depends_on = ["alloydb-auth-proxy"]
        env {
          name  = "ALLOYDB_INSTANCE"
          value = var.alloydb_instance
        }
        env {
          name  = "ALLOYDB_DATABASE"
          value = var.alloydb_database
        }
        env {
          name  = "ALLOYDB_USER"
          value = replace(module.specialized_parser_account.email, ".gserviceaccount.com", "")
        }
        env {
          name  = "PROCESSED_DOCS_BQ_PROJECT"
          value = google_bigquery_table.processed_documents.project
        }
        env {
          name  = "PROCESSED_DOCS_BQ_DATASET"
          value = google_bigquery_table.processed_documents.dataset_id
        }
        env {
          name  = "PROCESSED_DOCS_BQ_TABLE"
          value = google_bigquery_table.processed_documents.table_id
        }
        # env {
        #     name = "RUN_ID"
        #     value = "manual__2024-11-05T09:47:34+00:00"
        # }
        # env {
        #     name = "PROCESSOR_ID"
        #     value = "projects/dpu-1002/locations/us/processors/534f968cccf5f2b2"
        # }
        # env {
        #     name = "GCS_INPUT_PREFIX"
        #     value = "gs://dpu-process-dpu-1002/docs-processing-05-11-2024-rllop1c0/pdf-form/input"
        # }
        # env {
        #     name = "GCS_OUTPUT_URI"
        #     value = "gs://dpu-process-dpu-1002/docs-processing-05-11-2024-rllop1c0/pdf-form/output"
        # }
        # env {
        #     name = "BQ_TABLE"
        #     value = "dpu-1002.docs_store.docs_processing_05_11_2024_rllop1c0"
        # }
      }
      # containers {
      #   name = "alloydb-auth-proxy"
      #   image = "gcr.io/alloydb-connectors/alloydb-auth-proxy:latest"
      #   args = [
      #     var.alloydb_instance,
      #     "--address", "0.0.0.0",
      #     "--port", "5432",
      #     "--auto-iam-authn",
      #     "--psc"
      #   ]
      # }


    }
  }
}
