# Document Processing and Understanding
This repository is the source code for the Document Processing and Understanding (DPU) solution on Google Cloud. The solution is composed of modular components that collectively enable the creation of end-to-end workflow for document processing, management and analysis:

* **Document Ingestion:** Upload and import a variety of document types.
* **Document Processing:** Validate, extract information, and transform document content.
* **Document Storage:** Securely store and manage processed documents.
* **Document Indexing:** Enabling efficient search and retrieval of document information.
* **Search and Summarization:**  Search and summarization of document content.
* **Document Retrieval:** Access to the original document files.

## Get Started
To begin exploring the DPU solution, follow the step-by-step instructions in the [deployment guide](sample-deployments/composer-orchestrated-process/DEPLOYMENT.md). This guide details how to deploy the `Document Process and Understanding with Composer` sample on Google Cloud.

## Components
The solution comprises the following key components:

| Component | Description |
| -------------------------- | - |
| [Document Processing](components/processing/README.md) | Python tools and deployments for executing document processing tasks (extraction, transformation, enrichment). |
| [Common Infrastructure](components/common-infra/README.md) | Provides the shared infrastructure foundation for the DPU solution (networking, storage, datasets etc.). |
| [Workflow Orchestrator](components/dpu-workflow/README.md) | Orchestrates the end-to-end document processing workflow using Cloud Composer. |
| [Web UI](components/webui/README.md) | Offers a user interface for interacting with the DPU solution (search, summarization, document views etc). |

## Deployment Resources
[Reference Architecture](sample-deployments/composer-orchestrated-process/README.md) of the deployment sample.
