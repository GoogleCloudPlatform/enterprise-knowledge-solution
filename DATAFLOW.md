# Enterprise Knowledge Solution (EKS) Dataflow  
1. **Upload documents and trigger document processing workflow**  
    An employee (IT) manually uploads various document types (Excel, PDF, Word, Text, Outlook, .xlsx, .pdf, .docx) or a scheduled Cron Job triggers the upload. The uploaded files are stored in a designated "input" bucket within Google Cloud Storage.
    
    The upload to the "input" bucket triggers a Document Processing Workflow managed by Cloud Composer.
1. **Validate the documents:**  
    Documents that fail validation are redirected to a separate "reject" bucket within Google Cloud Storage for further review and handling.
1. **Initiate Processing Jobs:**  
    The workflow initiates specific processing jobs based on the document type:  
        ```PDF Classifier (Cloud Run -> Doc AI Custom Classifier):``` Identify PDF documents that contain forms.  
        ```Forms Processor (Cloud Run -> Doc AI Form Parser):``` Processes form documents(PDF).  
        ```Excel, Outlook Processor (Cloud Run):``` Processes Excel and Outlook files.  
1. **Extract and store content:**  
    Each processor extracts relevant content from the documents. The extracted content (pdf, docx, txt) is stored in a “process” bucket within Google Cloud Storage.  
1. **Create and store document metadata for Excel and Outlook documents:**  
    The extracted document metadata is stored in a BigQuery table.
1. **Utilize Document AI Batch API:**  
    The Document Processing Workflow leverages the Document AI Batch API for asynchronous processing of large document volumes.
1. **Create and store document metadata for forms in PDF documents:**  
    The extracted document metadata is stored in a BigQuery table.
1. **Data Serving:**  
    The processed and stored content from the "process" bucket is imported and indexed in Agent Builder’s BigQuery Data Store.
1. **Powering Search Applications:**  
    The extracted data stored in Agent Builder’s BigQuery Data Store is used to power search applications built with Vertex AI Agent Builder.
1. **Business User Access:**  
    Business Operations (Biz Ops) employees can access and interact with the processed data through a dedicated Web UI deployed in Cloud Run. This UI leverages the search and summarization capabilities of the Vertex AI Agent Builder.
