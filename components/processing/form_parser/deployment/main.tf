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
  dpu_label = {
    goog-packaged-solution : "eks-solution"
  }
}

resource "google_document_ai_processor" "docai-form-processor" {
  location     = var.location
  display_name = var.docai_form_processor_name
  type         = "FORM_PARSER_PROCESSOR"
}

resource "google_service_account" "dpu_run_service_account" {
  account_id   = var.dpu_run_service_account
  display_name = var.dpu_run_service_account_display_name
}

resource "google_project_iam_member" "bigquery_data_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.dpu_run_service_account.email}"
}

resource "google_project_iam_member" "documentai_editor" {
  project = var.project_id
  role    = "roles/documentai.editor"
  member  = "serviceAccount:${google_service_account.dpu_run_service_account.email}"
}

resource "google_project_iam_member" "storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.dpu_run_service_account.email}"
}

resource "google_alloydb_user" "form_parser_user" {
  cluster   = var.alloydb_cluster_name
  user_id   = google_service_account.dpu_run_service_account.email
  user_type = "ALLOYDB_IAM_USER"

  database_roles = ["alloydbiamuser"]
}

resource "google_cloud_run_v2_job" "docai-form-processor-job" {
  name     = var.form_parser_cloud_run_job_name
  location = var.region

  template {
    labels = local.dpu_label
    template {
      service_account = google_service_account.dpu_run_service_account.email
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/dpu-form-parser-repo/dpu-form-processor:latest"
        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }
        env {
          name  = "LOCATION"
          value = var.location
        }
        env {
          name  = "PROCESSOR_ID"
          value = google_document_ai_processor.docai-form-processor.name
        }
        env {
          name = "GCS_OUTPUT_PREFIX"
          # Pass value from composer
          value = "gs://${var.gcs_output_prefix}/pdf-forms/output"
        }
        env {
          name  = "GCS_INPUT_PREFIX"
          value = "gs://${var.gcs_input_prefix}/pdf-forms/input"
        }
        env {
          name = "BQ_TABLE_ID"
          # Pass value from composer @todo remove this table once composer is integrated
          value = "prj-14-376417.docs_store.sample-2"
        }
      }
    }
  }
}

