# DPU Cloud Composer orchestrated document processing
In this directory, you can find an end-to-end example deployment of the Document Processing and Understanding (DPU) solution on Google Cloud. 

## Architecture
The following diagram describes the architecture that you create with this deployment:
![alt text](../../assets/deployment-architecture.png)

Which showcases how all DPU components integrate to create a complete workflow for:

* **Document Ingestion:** Uploading and importing various document types. (The blue box)
* **Document Processing:** Validation, extraction and transformation of document content. (The red boxes)
* **Document Storage:** Secure storage and management of processed documents. (The green box)
* **Document Indexing:** Enabling efficient search and retrieval of document information. (Agent Builder Data Store)
* **Search and Summarization:**  Search and summarization of document content. (Agent Builder Search App)
* **Document Retrieval:** Access to the original document files. (Web UI)

The deployment helps you to create and configure the following DPU components:

| Component | Description |
| -------------------------- | - |
| [common-infra](../../components/common-infra/README.md) | Provides the shared infrastructure for the DPU solution (networking, storage, datasets etc.). |
| [doc-processing](../../components/processing/README.md) | Handles document processing tasks (extraction, transformation, enrichment). |
| [workflow-orchestrator](../../components/dpu-workflow/README.md) | Orchestrates the end-to-end document processing workflow using Cloud Composer. |
| [web-ui](../../components/webui/README.md) | Offers a user interface for interacting with the DPU solution (search, summarization, document views etc). |

**Note:** Each of these components can be deployed individually or as part of a custom setup. The [`main.tf`](./main.tf) file demonstrates how to configure and deploy each component using Terraform.

### Additional Resources
In additional to the DPU components this example also deployes the following resources:
| Name | Description |
|------|-------------|
| [Agent Builder Data Store](https://cloud.google.com/dialogflow/vertex/docs/concept/data-store) | The data store where processed documents are collected and indexed. This is the backbone that powers the search and summarization capabilities. |
| [Agent Builder Search App](https://cloud.google.com/generative-ai-app-builder/docs/create-datastore-ingest) | A generic Agent Builder search app that provides the API interface for searching documents in the Data Store. |

## Get Started
Follow the [Deployment Guide](DEPLOYMENT.md)

## Next steps
Follow the [Usage Guide](USE.md)
