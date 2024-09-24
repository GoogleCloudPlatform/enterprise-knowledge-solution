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
  ui_service_name     = "eks-ui"
  cloud_build_fileset = setunion(fileset(path.module, "../src/**"), fileset(path.module, "../Dockerfile"), fileset(path.module, "../requirements.txt"))
  cloud_build_content_hash = sha512(join(",", [
  for f in local.cloud_build_fileset : fileexists("${path.module}/${f}") ? filesha512("${path.module}/${f}") : sha512("file-not-found")]))
}

resource "local_file" "cloudbuild_config" {
  filename = "${path.module}/build/cloudbuild.yaml"
  content = templatefile("${path.module}/build/cloudbuild.yaml.template", {
    project_id            = var.project_id,
    build_service_account = var.cloud_build_service_account_email,
    image_tag             = "${var.region}-docker.pkg.dev/${module.project_services.project_id}/${var.artifact_repo}/${local.ui_service_name}"
  })
}

# Build and upload the app container
module "app_build" {
  source = "github.com/terraform-google-modules/terraform-google-gcloud?ref=db25ab9c0e9f2034e45b0034f8edb473dde3e4ff" # commit hash of version 3.5.0

  create_cmd_entrypoint = "gcloud"
  create_cmd_body       = "builds submit --region ${var.region} --project ${var.project_id} --config \"${local_file.cloudbuild_config.filename}\" \"${path.module}/../../..\""
  enabled               = true

  create_cmd_triggers = {
    source_contents_hash = local.cloud_build_content_hash
  }
}
