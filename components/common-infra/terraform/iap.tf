/*
 * IAP Configuration
 */



# OAuth Client
resource "google_iap_client" "project_client" {
  display_name = "Enterprise Knowledge ADP client"
  brand        = "projects/${data.google_project.project.number}/brands/${data.google_project.project.number}"
}

#resource "google_project_iam_member" "iap_users" {
#  for_each = toset(var.iap_access_domains)
#  project  = module.project_services.project_id
#  role     = "roles/iap.httpsResourceAccessor"
#  member   = each.key
#}

resource "google_project_service_identity" "iap_sa" {
  provider = google-beta
  project  = module.project_services.project_id
  service  = "iap.googleapis.com"
}

data "google_iam_policy" "reader" {
  binding {
    role = "roles/iap.httpsResourceAccessor"
    #TODO: expose this as a variable not hardcoded
    members = [
      "group:eks-readers-1@ellioteaton.altostrat.com",
    ]
  }
}

data "google_iam_policy" "uploader" {
  binding {
    role = "roles/iap.httpsResourceAccessor"
    members = [
      "group:eks-uploaders@ellioteaton.altostrat.com",
    ]
  }
}

resource "google_iap_web_backend_service_iam_policy" "policy1" {
  project = var.project_id
  #TODO: remove the hardcoding, need to bring outputs from other module.dpu_ui as a var
  web_backend_service = "eks-ui-lb-backend-backend1"
  policy_data         = data.google_iam_policy.reader.policy_data
}

resource "google_iap_web_backend_service_iam_policy" "policy2" {
  project = var.project_id
  #TODO: remove the hardcoding, need to bring outputs from other module.dpu_ui as a var
  web_backend_service = "eks-ui-lb-backend-backend2"
  policy_data         = data.google_iam_policy.uploader.policy_data
}

