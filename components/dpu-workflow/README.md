# DPU Document Workflow Orchestrator
This module provisons the resources required to run the DPU document workflow orchestrator. The document workflow is a airflow DAG running on Cloud Composer. 
The orchestrator carries out the following task for the processing of the ingested documents in DPU.
- Move the ingested documents from the cloud storage input bucket to process bucket
- Creates folders in cloud storage process bucket and reject bucket for the current workflow run
- Creates a BigQuery table for the current workflow run
- Starts the DPU doc-processer job on Cloud Run to process the ingested documents
- Import the processed document into Vertex AI Agent Builder data store

## Resource Created
Following resource are provsioned and created when the module are applied through terraform:
| Name | Description |
|------|-------------|
| VPC Subnet | A VPC subnet in the common DPU network. The VPS subnet has secondary IP ranges dedicated the the Cloud Composer environment |
| Cloud Composer environmet `dpu-composer` | A Cloud Composer environment for execution of the document workflow orchestrator |
| Document Workflow DAG | The document workflow DAG source code deployed in to the Cloud Composer DAG bucket, ready for DPU users to run |
| Workflow Service Account | Dedicated service accout used in the workflow execution with the neccessary access right needed to GCS bucket, BigQuery dataset, Cloud Run and Vertex AI Agent builder |

## Inputs

| Name | Description |
|------|-------------|
| project_id | Google Cloud project where document workflow resource are provisioned |
| vpc_network_name | The name of the DPU common VPC network |
| vpc_network_id | The ID of the DPU common VPC network |
| region | Google Cloud region where the resources are provioned, used the same value as the common infra module, to avoid inter regional traffic |
| composer_version | (Optional) Specify a Cloud Composer version, default: `composer-2.8.1-airflow-2.7.3`|
| composer_env_variables | Key value pair of env variable to be set in the Cloud Composer environment, that required by the workflow orchestrator DAG. For details on which variables are set set the [sample deployment](../../sample-deployments/composer-orchestrated-process/main.tf) |
| composer_additional_pypi_packages | (Optional) Additional PyPi package to install on the Cloud Composer environment, default: `google-cloud-discoveryengine = ">=0.11.11"` |
| composer_environment_size | (Optional) Cloud Composer environment size, default: `ENVIRONMENT_SIZE_SMALL` |
| composer_sa_roles | (Optional) Service account roles  enabled on the workflow run account, default: `roles/composer.worker, roles/iam.serviceAccountUser, roles/bigquery.dataEditor, roles/run.developer, roles/discoveryengine.editor, roles/documentai.apiUser`|

## Output
| Name | Description |
|------|-------------|
| composer_dag_gcs_bucket | DAG Cloud Storage bucket for the Cloud Compoer Environment, where DAG source file can be dropped in to and makes the workflow available in the Cloud Composer environemtn. |