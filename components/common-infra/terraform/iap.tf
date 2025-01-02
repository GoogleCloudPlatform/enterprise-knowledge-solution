/*
 * IAP Configuration
 */



# OAuth Client
resource "google_iap_client" "project_client" {
  display_name = "Enterprise Knowledge ADP client"
  brand        = "projects/${data.google_project.project.number}/brands/${data.google_project.project.number}"
}

resource "google_project_iam_member" "iap_users" {
  for_each = toset(var.iap_access_domains)
  project  = module.project_services.project_id
  role     = "roles/iap.httpsResourceAccessor"
  member   = each.key
}

resource "google_project_service_identity" "iap_sa" {
  provider = google-beta
  project  = module.project_services.project_id
  service  = "iap.googleapis.com"
}