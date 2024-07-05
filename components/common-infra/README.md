# Common Infra module
The module provisions the common resource required by the Document Processing & Understand (DPU) solution, which include the following:
| Name | Description |
|------|-------------|
| BigQuery `docs_store` Dataset | A dataset where the parsed document metadata are store and used as input to Agent Build Data Store  |
| Google Cloud Storage `docs-input` Bucket | Storage bucket for users of DPU to drop document for ingestion to the solutions |
| Google Cloud Storage `dpu-process` Bucket | Storage bucket used by document processing workflow to store the ingested documents |
| Google Cloud Storage `dpu-reject` Bucket | Storage bucket used by document processing workflow to store the documents which have been failed to parse |
| Artifact Registry `dpu-docker-repo` | Container repository for hosting of custom containers userd by DPU |
| VPC Network `dpu-network` | Common VPC network for the DPU solution |

## Inputs

| Name | Description |
|------|-------------|
| project_id | Google Cloud project where the common resources for DPU are provisioned |
| region | Google Cloud region where the resources are provioned, i.e. `us-central1`, `europe-west1` etc |
| bq_store_dataset | (Optional) Dataset name for the document store, default : `docs_store` |

## Output
| Name | Description |
|------|-------------|
| artifact_repo | The artifict registry object representaing the repositoy being created|
| bq_store_dataset_id | The ID of the docs_store dataset being created |
| gcs_input_bucket_name | GCS bucket name for the input bucket |
| gcs_process_bucket_name | GCS bucket name for the process bucket |
| gcs_reject_bucket_name | GCS bucket name for the reject bucket |
| project_id | The project under which all the resources are being created |
| vpc_network_id | The ID of the common VPC network being created |
| vpc_network_name | The name of the common VPC network being created |
