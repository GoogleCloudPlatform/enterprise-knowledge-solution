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
  location = var.location
  display_name = var.docai_form_processor_name
  type = "FORM_PARSER_PROCESSOR"
}

resource "google_cloud_run_v2_job" "docai-form-processor-job" {
  name     = var.cloud_run_job_name
  location = var.region

  template {
    template {
      containers {
        image = "us-central1-docker.pkg.dev/prj-14-376417/dpu-form-parser-repo/dpu-form-processor@sha256:9c07c155a1d5c384f308b4b97e81fe76d45aa2fb20199152351f300725d4ebfe"
        env {
          name = "PROJECT_ID"
          value = var.project_id
        }
        env {
          name = "LOCATION"
          value = var.location
        }
        env {
          name = "PROCESSOR_ID"
          value = google_document_ai_processor.docai-form-processor.name
        }
        env {
          name = "GCS_OUTPUT_PREFIX"
          value = "gs://${var.gcs_output_prefix}/"
        }
        env {
          name = "GCS_INPUT_PREFIX"
          value = "gs://${var.gcs_input_prefix}/pdf-forms/"
        }
      }
    }
  }
}

