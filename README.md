# Enterprise Knowledge Solution (EKS)

This repository contains the source code to implement the Enterprise Knowledge Solution (EKS) on the Google Cloud Platform (GCP). The solution comprises modular components that collectively enable the creation of end-to-end workflow for document processing, management, and analysis:

- **Document Ingestion:** Upload and import a variety of document types.
- **Document Processing:** Validate, extract information, and transform document content.
- **Document Storage:** Securely store and manage processed documents.
- **Document Indexing:** Enabling efficient search and retrieval of document information.
- **Search and Summarization:** Search and summarization of document content.
- **Document Retrieval:** Access to the original documents that contibuted to the search results and summaries.

## Components

The solution consists of the following key components:

| Component                                                        | Description                                                                                       |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| [Common Infrastructure](components/common-infra/README.md)       | Provides the shared infrastructure foundation for the EKS (networking, storage, datasets etc.).   |
| [Workflow Orchestrator](components/dpu-workflow/README.md)       | Orchestrates the end-to-end document processing workflow using Cloud Composer.                    |
| [Document Classifier](components/doc-classifier/README.md)       | Identifies document top                                                                           |
| [MS Office Document Processing](components/processing/README.md) | Prepare Outlook, Excel and ZIP files for Search and Summarization.                                |
| Specialized Parser                                               | Processes forms, invoices, and other documents using Document AI.                                 |
| [Web UI](components/webui/README.md)                             | Offers a user interface for interacting with the EKS (search, summarization, document views etc). |
| Post-setup config                                                | Connects to the AlloyDB resource and configures postgres schemas, tables, and roles.              |

## Solution Architecture

![Solution Architecture](assets/deployment-architecture.png "Solution Architecture")
The above diagram shows how the documents uploaded into the Google Cloud Storage bucket are processed and prepared for search and summarization. For more details, see [DATAFLOW](DATAFLOW.md).

## Enterprise Foundations

This Solution assumes that you have already configured an enterprise-ready foundation.
The foundation is not a technical prerequisite (meaning, you can use the [deployment guide](#deployment-guide) without a foundation).
However, we recommend building an enterprise-ready foundation before releasing production workloads with sensitive data.

For more details, see [Deploying Solutions to an enterprise-ready foundation](docs/foundation.md)

## Deployment Guide

This section provides step-by-step instructions for deploying the `Enterprise Knowledge Solution` on Google Cloud using Terraform.

### Deploy infrastructure-as-Code resources

To deploy the Infrastructure-as-Code (IaC) resources needed for this solution, perform the follow steps:

1. [Create or select a Google Cloud project](https://cloud.google.com/resource-manager/docs/creating-managing-projects) and ensure that [billing is enabled for your Google Cloud project](https://cloud.google.com/billing/docs/how-to/verify-billing-enabled#console).

1. This example code is deployed through Terraform using the identity of a least privilege service account. Your user identity needs the following [IAM Roles](https://cloud.google.com/iam/docs/roles-overview) on your project to create this service account and validate other requirements with a setup script:

   - Project IAM Admin
   - Role Admin
   - Service Account Admin
   - Service Usage Admin

1. To deploy the solution from this repository using an online terminal with software and authentication preconfigured, use [Cloud Shell](https://shell.cloud.google.com/?show=ide%2Cterminal).
   Alternatively, to deploy this repository using a local terminal:

   - [install](https://cloud.google.com/sdk/docs/install) and [initialize](https://cloud.google.com/sdk/docs/initializing) the gcloud CLI
   - [install Terraform](https://developer.hashicorp.com/terraform/tutorials/gcp-get-started/install-cli)
   - [install the Git CLI](https://github.com/git-guides/install-git)

1. In Cloud Shell or your preferred terminal, clone this repository:

   ```sh
   git clone https://github.com/GoogleCloudPlatform/enterprise-knowledge-solution.git
   ```

1. Navigate to the Sample Directory:

   ```sh
   cd <YOUR_REPOSITORY>/sample-deployments/composer-orchestrated-process
   ```

   Where `<YOUR_REPOSITORY>` is the path to the directory where you cloned this repository.

1. Set the following environment variables:

   ```sh
   export PROJECT_ID="<your Google Cloud project id>"
   export REGION="<Google Cloud Region for deploying the resources>"
   export IAP_ADMIN_ACCOUNT="the email of the group or user identity displayed as the support_email field on Oauth consent screen. This must be either the email of the user running the script, or a group of which they are Owner."
   ```

   - (Optional) By default, this repository automatically creates and uses a service account `deployer@$PROJECT_ID.iam.gserviceaccount.com` to deploy Terraform resources. The necessary IAM policies and roles are automatically configured in the setup script to ease the deployment. If you have a service account in your existing terraform pipeline that you want to use instead, additionally set the optional environment variables to configure your custom deployer service account with the least privilege IAM roles:

     ```sh
     export SERVICE_ACCOUNT_ID="your existing service account identity to be used for Terraform."
     ```

1. Run the following script to set up your GCP project before running Terraform.

   ```sh
   scripts/pre_tf_setup.sh
   ```

   This setup script does the following:

   - Validate software dependencies
   - Enable the required APIs defined in `project_apis.txt`
   - Enable the required IAM roles on the service account you'll use to deploy Terraform resources, defined in `persona_roles_DEPLOYER.txt`
   - Set up the OAuth consent screen (brand) required for IAP. We recommend you create this resource using a user identity instead of a service account. This approach helps avoid problems related to [support_email ownership](https://cloud.google.com/iap/docs/programmatic-oauth-clients#:~:text=the%20user%20issuing%20the%20request%20must%20be%20an%20owner%20of%20the%20specified%20support%20email%20address) and [destroying a terraform-managed Brand resource](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/iap_brand).
   - Enables the required IAM roles used for underlying Cloud Build processes
   - Authenticate [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials) with your service account credentials to be used by Terraform.
   - Triggers a pop-up dialog box: 'Sign in with Google' prompting you to authenticate the Google Auth Library. Follow the directions to authenticate with your user account, which will then configure Application Default Credentials (ADC) using the impersonated service account credentials to be used by Terraform.

1. Create a terraform.tfvars file with the following variables:

   | Terraform variables         | Description                                                                                           |
   | --------------------------- | ----------------------------------------------------------------------------------------------------- |
   | project_id                  | Your Google Cloud project ID.                                                                         |
   | region                      | The desired region for deploying single-region resources (e.g., "us-central1", "europe-west1").       |
   | vertex_ai_data_store_region | The multiregion for your Agent Builder Data Store, the possible values are ("global", "us", or "eu"). |
   | docai_location              | Sets the location for Document AI                                                                     |
   | webui_domains               | Your domain name for Web UI access (e.g., ["webui.example.com"])                                      |
   | iap_access_domains          | List of domains granted for IAP access to the Web UI (e.g., ["domain:example.com"])                   |

1. (Optional) By default, the Terraform script creates a new VPC network in the same project as other resources. You can use an existing VPC network instead by configuring the following optional terraform variables.

   | Terraform variables | Description                                    |
   | ------------------- | ---------------------------------------------- |
   | create_vpc_network  | false # default is true                        |
   | vpc_name            | The name of your existing vpc, (e.g., "myvpc") |

1. Initialize Terraform:

   ```sh
   terraform init
   ```

1. Review the proposed changes and apply them:

   ```sh
   terraform apply
   ```

   The provisioning process may take approximately an hour to complete.

1. Migrate Terraform state to the remote Cloud Storage backend:

   ```sh
   terraform init -migrate-state
   ```

   Terraform detects that you already have a state file locally and prompts you to migrate the state to the new Cloud Storage bucket. When prompted, enter `yes`.

### Train a custom Document AI classifier

Some workflows depend on a [custom classifier](https://cloud.google.com/document-ai/docs/custom-classifier) trained in Document AI, which is not automatically deployed by this repository. To create, train, and deploy your own custom classifier, do the following:

1. Create a Google Cloud Storage bucket to hold your test documents, divided into subfolders `gs://<YOURBUCKET>/form`, `gs://<YOURBUCKET>/invoice`, `gs://<YOURBUCKET>/general`.

   - For best results, we recommend that you use forms and invoices representative of the types of documents you will ingest. However, you can also use the [test documents and forms provided in this repostiroy](sample-deployments/composer-orchestrated-process/documents-for-testing/forms-to-train-docai) as a generic starting point. These documents have been generated with synthetic data.

1. In the Google Cloud console, navigate to Document AI > My Processors > Create Custom Processor. When presented with types of custom processors, choose "Custom Classifier". Give it a name and choose the same location where you have deployed other EKS resource, then click "Create".

1. Under the "Processor Details" tab, click "Configure Your Dataset". DocAI will create an empty Google Cloud Storage bucket for the training, you can accept the default and continue. Click "Import Documents". On the pop-up to "select a source folder on Cloud Storage":

   - For "source path", configure the source path for each of the three folders created in a previous step `gs://<YOURBUCKET>/form`, `gs://<YOURBUCKET>/invoice`, and `gs://<YOURBUCKET>/general`.
   - For "document labels", use the same value as the folder name, `form`, `invoice`, `general`.
   - For "data split", choose "auto-split".
   - Click import when finished entering the previous fields

   _Note: out of the box, this solution supports the `form` and `invoice` labels only. Any other label will cause the workflow to treat a document as a generic document and it will not extract structured data._

1. Wait for the confirmation that the import process has finished before proceeding.

1. Click "Train New Version" and give the version any name. After you click "start training", the process might take several hours to complete.

1. After the version is done training, go to the "Manage Versions" tab, click on the three dot menu for your version and click "deploy version". This might take several minutes to complete.

1. After deployment is complete, click the three dot menu again and choose "set as default".

1. After all steps to train and deploy the customer classifier are complete, add the following variable to your `terraform.tfvars` and run `terraform apply` again.

   | Terraform variables  | Description                                                                                                                                                                     |
   | -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
   | custom_classifier_id | projects/<CLASSIFIER_PROJECT>/locations/<CLASSIFIER_LOCATION>/processors/<CLASSIFIER_ID>. The value of <CLASSIFIER_ID> must be the alphanumeric ID, not the user-friendly name. |

### (Optional) Configure access to the Web UI search application

_Note: This step is optional because you can preview the search results on the [Agent Builder Preview](https://cloud.google.com/generative-ai-app-builder/docs/preview-search-results) without completing this step._

This step configures a sample Web UI for a custom search application based on Agent Builder.
You must own a domain name used to access the web application, and be able to configure DNS records at your domain registratrar. The previous terraform steps have provisioned a load balancer and a managed SSL certificate for your domain to route web traffic securely to the Web-UI application. Authentication to the application is managed by an [Identity-Aware Proxy](https://cloud.google.com/iap/docs/concepts-overview)

1. Verify the external IP configured for the load balancer ingress:

   ```sh
   terraform output webui_dns_config
   ```

1. On your DNS provider, configure the `A` records to map the domain name of your application to the external IP.

1. Review the [Oauth Consent screen](https://support.google.com/cloud/answer/10311615?hl=en) that will be displayed to IAP users, and [enable IAP for Cloud Run](https://cloud.google.com/iap/docs/enabling-cloud-run#configuring_to_limit_access).

1. Validate that the setup is correct by accessing the domain from your web browser and authenticating to the app with your Google credentials.

## User Guide

After successfully completing the steps in thge previous section Deployment Guide, you can test the entire EKS workflow.

### Upload Documents

1. Get the Input Bucket Name:

   ```sh
   terraform output gcs_input_bucket_name
   ```

   This command will display the name of the Cloud Storage bucket designated for uploading documents.

1. Open the Input Bucket:

   - Go to the [Cloud Storage console](https://console.cloud.google.com/storage)
   - Locate the input bucket using the name obtained in the previous step.

1. Upload Your Documents:
   - Click the "Upload Files" button or drag and drop your files into the bucket. Supported file types:
     - MS Outlook (msg)
     - MS Excel (xlsx, xlsm)
     - MS Word (docx)
     - MS PowerPoint (pptx)
     - PDF with text only content
     - PDF with forms
     - HTML
     - TXT
     - ZIP containing any of above supported file types

### Trigger the document processing workflow

Airflow workflows must be triggered to process the uploaded documents.

To trigger the workflow using an automatable script:

1. Execute the following bash script:

   ```sh
   scripts/trigger_workflow.sh
   ```

Alternatively, to trigger the workflow using the Airflow UI:

1. Get the Cloud Composer Airflow URI:

   ```sh
   terraform output composer_uri
   ```

   This command will display the web interface URI of the Cloud Composer Airflow environment.

1. Access the Airflow UI:

   - Open your web browser and navigate to the URI obtained in the previous step.
   - Authenticate with your Google Cloud credentials.

1. Trigger the Workflow:

   - In the Airflow UI, locate the DAG (Directed Acyclic Graph) named: `run_docs_processing`, which represents the document processing workflow.
   - Click the "Trigger DAG" button to access the trigger page. Here, you can view the input parameters for the workflow.
   - Leave the default parameters as they are and click the "Trigger" button to initiate the workflow.

1. Monitor Execution Progress:
   - Navigate to the DAG details view using the URL:
     `<composer_uri>/dags/run_docs_processing` (replace `<composer_uri>` with the URI you obtained earlier).
   - This page displays the progress of each task in the workflow, along with logs and other details.

### Search and Explore the processed documents

Once the workflow completes successfully, all documents will be imported into the Vertex AI Agent Builder Data Store named `eks-data-store`.

1. Get the Agent Build App URI:

   ```sh
   terraform output agent_app_uri
   ```

1. Access the Agent Build App console:

   - Open your web browser and navigate to the URI obtained in the previous step.

1. Search and Explore:
   - On the console page, you'll find an input bar. Enter your questions or queries related to the documents you've uploaded.
   - The app will provide summarized answers based on the content of your documents, along with references to the specific source documents.

### Search and Explore from EKS Web UI

\_Note: This section only applies if you completed the "configure access to the Web UI search application" step under the deployment guide.

The Web UI is an example of how you extend the basic functionality of the Agent Builder application into a user interface that employees access to query documents. For more information on the Web UI component, please refer to its [Readme](./components/webui/README.md).

1. Access the EKS Web UI:

   - Open your web browser and navigate to domain address which you have configured for the WebUI.
   - Authenticate with your Google Cloud credentials

1. Search and Explore:
   - In the `Search Documents` page, enter your questions or queries related to the documents you've uploaded and press enter to get summarized answers, along with references to the specific source documents.
   - In the `Browse Documents` page, explore and view the documents stored in the Data Store.

### Delete a document from EKS

When you need to remove a document from the scope of search and summarization, do the following:

1. Identify the document you want to delete:

   - Open Agent Builder Datastore and note down the ID and URI of the document that you want to delete from DP&U.
   - Make sure the file in the URI exists in the Google Cloud Storage bucket
   - Please note that this script will not delete the GCS Folder that contains the file
   - Based on the URI, identify and note down the name of the BQ Table that contains the document metadata
   - Please note that this script will not delete the BQ Table that contains the document metadata

1. Execute the following command to find a documents from the Agent Builder Datastore:

   ```sh
   scripts/find_document.sh <DOC_ID>
   ```

1. Execute the following command to delete a single document:

   ```sh
   scripts/delete_doc.sh [-p <PROJECT_ID>] -l <LOCATION> -u <DOC_URI> -t <BQ_TABLE> -d <DOC_ID>
   ```

1. Execute the following command to delete a batch of documents:

   ```sh
   scripts/delete_doc.sh [-p <PROJECT_ID>] -l <LOCATION> -b <BATCH_ID>
   ```

1. Execute the following command to delete all documents from the Agent Builder Datastore:

   ```sh
   scripts/reset_datastore.sh [-p <PROJECT_ID>] -l <LOCATION>
   ```

### Upgrade your environment with new versions

When new releases of EKS are code are available, you can update your infrastructure by pulling the latest changes from this repository and running the following commands again:

```sh
scripts/pre_tf_setup.sh
terraform init
terraform apply
```

We provide no guarantees that in-place upgrades of your infrastructure as code resources to new code versions can be completed without destroying and recreating some resources. Where infrastructure resources have changed significantly between versions, you might encounter terraform state errors that require troubleshooting with state manipulation commands like [taint](https://developer.hashicorp.com/terraform/cli/commands/taint) or [move](https://developer.hashicorp.com/terraform/cli/state/move).
