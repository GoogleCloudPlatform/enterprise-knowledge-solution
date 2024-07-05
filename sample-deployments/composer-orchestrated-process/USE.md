# Usage Guide
This guide provides step-by-step instructions on how to use the `Document Process and Understanding with Composer` deployed on Google Cloud.
After successful [deployment](DEPLOYMENT.md), you can test the entire DPU workflow.

## Upload Documents
1. Get the Input Bucket Name:
    ```sh
    terraform output gcs_input_bucket_name
    ```
    This command will display the name of the Cloud Storage bucket designated for uploading documents.

1. Open the Input Bucket:
    * Go to the [Cloud Storage console](https://console.cloud.google.com/storage) 
    * Locate the input bucket using the name obtained in the previous step.

1. Upload Your Documents:
    * Click the "Upload Files" button or drag and drop your files into the bucket. Supported file types:
      - MSF Outlook (msg)
      - MSF Excel(xlsx, xlsm)
      - PDF
      - HTML
      - TXT
      - ZIP (zip) containing any of above supported file types
## Run the document processing Workflow
1. Get the Cloud Composer Airflow URI:
    ```sh 
    terraform output composer_uri
    ```
    This command will display the web interface URI of the Cloud Composer Airflow environment.
1.  Access the Airflow UI:
    * Open your web browser and navigate to the URI obtained in the previous step.
    * First time y will need to authenticate with your Google Cloud credentials.
1. Trigger the Workflow:
    * In the Airflow UI, locate the DAG (Directed Acyclic Graph) named: `run_docs_processing`, which represents the document processing workflow.
    * Click the "Trigger DAG" button to access the trigger page. Here, you can view the input parameters for the workflow.
    * Leave the default parameters as they are and click the "Trigger" button to initiate the workflow.
1. Monitor Execution Progress:
    * Navigate to the DAG details view using the URL:
    `<composer_uri>/dags/run_docs_processing`  (replace `<composer_uri>` with the URI you obtained earlier).
    * This page displays the progress of each task in the workflow, along with logs and other details.

## Search and Explore the processed documents
Once the workflow completes successfully, all documents will be imported into the Vertex AI Agent Builder Data Store named Document Processing & Understanding`.
1. Get the Agent Build App URI:
    ```sh 
    terraform output agent_app_uri
    ```
1.  Access the Agent Build App console:
    * Open your web browser and navigate to the URI obtained in the previous step.
1. Search and Explore:
    * On the console page, you'll find an input bar. Enter your questions or queries related to the documents you've uploaded.
    * The app will provide summarized answers based on the content of your documents, along with references to the specific source documents.

## Search and Explore from DPU Web-UI
1. Get the DPU Web-UI URI:
    ```sh 
    terraform output web_ui_uri
    ```
1.  Access the DPU Web-UI:
    * Open your web browser and navigate to the URI obtained in the previous step.
    * First time y will need to authenticate with your Google Cloud credentials
1. Search and Explore:
    * In the `Search Documents` page, enter your questions or queries related to the documents you've uploaded and press enter to get summarized answers, along with references to the specific source documents.
    * In the `Browse Documents` page, explore and view the documents stored in the Data Store.

For more information on the Web-UI component, please refer to its [README](../../components/webui/README.md).
