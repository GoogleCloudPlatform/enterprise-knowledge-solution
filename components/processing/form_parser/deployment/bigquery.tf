resource "google_bigquery_table" "form_values" {
  project = var.project_id
  dataset_id = var.bq_dataset_id
  table_id = "form_values"

  deletion_protection = true

  schema = file("${path.module}/form_values_table.json")
}
