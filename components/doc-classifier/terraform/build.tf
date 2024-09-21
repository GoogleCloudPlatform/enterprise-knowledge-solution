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
  cloud_build_fileset = fileset("${path.module}/src/", "**/*")
  cloud_build_content_hash = sha512(join("", [for f in local.cloud_build_fileset : fileexists(f) ? filesha512(f) :
  sha512("file-not-found")]))
  service_account_name = var.classifier_cloud_run_job_name
}

# See github.com/terraform-google-modules/terraform-google-gcloud
module "gcloud" {
  source                = "github.com/terraform-google-modules/terraform-google-gcloud?ref=db25ab9c0e9f2034e45b0034f8edb473dde3e4ff" # commit hash of version 3.5.0
  create_cmd_entrypoint = "gcloud"
  create_cmd_body       = <<-EOT
    builds submit ${path.module}/../src \
      --pack image=${local.image_name_and_tag} \
      --project $PROJECT_ID \
      --region $REGION
  EOT
  enabled               = true

  create_cmd_triggers = {
    source_contents_hash = local.cloud_build_content_hash
  }
}
