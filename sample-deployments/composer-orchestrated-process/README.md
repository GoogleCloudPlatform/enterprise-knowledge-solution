# DPU Cloud Composer orchestrated document processing
In this directory, you can find an end-to-end example deployment of the Document Processing and Understanding (DPU) solution on Google Cloud. 

The DP&U components can be deployed individually or as part of a custom setup. The [`main.tf`](./main.tf) file demonstrates how to configure and deploy each component using Terraform.

### Additional Resources
In additional to the DPU components this example also deployes the following resources:
| Name | Description |
|------|-------------|
| [Agent Builder Data Store](https://cloud.google.com/dialogflow/vertex/docs/concept/data-store) | The data store where processed documents are collected and indexed. This is the backbone that powers the search and summarization capabilities. |
| [Agent Builder Search App](https://cloud.google.com/generative-ai-app-builder/docs/create-datastore-ingest) | A generic Agent Builder search app that provides the API interface for searching documents in the Data Store. |

## Get Started with the Deployment Guide
Follow the [Deployment Guide](../../README.md#deployment-guide)
