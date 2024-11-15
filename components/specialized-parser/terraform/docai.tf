resource "google_document_ai_processor" "eks-invoice-processor" {
  location     = var.processors_location
  display_name = "eks-invoice-processor"
  type         = "INVOICE_PROCESSOR"
}

resource "google_document_ai_processor" "eks-form-processor" {
  location     = var.processors_location
  display_name = "eks-form-processor"
  type         = "FORM_PARSER_PROCESSOR"
}
