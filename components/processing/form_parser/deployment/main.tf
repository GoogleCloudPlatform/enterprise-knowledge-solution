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


resource "google_document_ai_processor" "docai-form-processor" {
  location     = var.location
  display_name = var.docai_form_processor_name
  type         = "FORM_PARSER_PROCESSOR"
}

resource "google_cloud_run_v2_job" "docai-form-processor-job" {
  name     = var.cloud_run_job_name
  location = var.region

  template {
    template {
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
          name  = "GCS_OUTPUT_PREFIX"
          value = "gs://${var.gcs_output_prefix}/pdf-forms/output"
        }
        env {
          name  = "GCS_INPUT_PREFIX"
          value = "gs://${var.gcs_input_prefix}/pdf-forms/input"
        }
      }
    }
  }
}

