# Enterprise Knowledge Solution (EKS) Dataflow

1. **Upload documents and trigger document processing workflow**
   An employee (IT) manually uploads various document types (Excel, PDF, Word, Text, Outlook) or a scheduled Cron Job triggers the upload. The uploaded files are stored in a designated "input" bucket within Google Cloud Storage.
   
   The upload to the "input" bucket triggers a Document Processing Workflow managed by Cloud Composer.  
1. **Validate the documents:**
   Documents that fail validation are redirected to a separate "reject" bucket within Google Cloud Storage for further review and handling.
1. **Initiate Processing Jobs:**
   The workflow initiates specific processing jobs based on the document type:
   - `Document Classifier (Cloud Run -> Doc AI Custom Classifier):`  Identify PDF document type (Any form, bank statements, invoices, pay slip, lending doc and utility bills)  
   - `Specialized Parser (Cloud Run -> Doc AI Form and Specialied Parser):` Processes forms and documents (Any form, bank statements, invoices, pay slip, lending doc and utility bills)  
   - `Excel, Outlook Processor (Cloud Run):` Processes Excel and Outlook files.  
1. **Utilize Document AI Batch API:**
   The Specialized Parser Job leverages Document AI Batch API for asynchronous processing of large document volumes.
1. **Extract and store data elements:**
   The Specialized Parser Job uses Document AI Batch API to extract data elements from the documents and stores the extracted data elements in AlloyDB, BigQuery and Firestore.  
1. **Create and store document metadata in BigQuery for Search and Summarization:**
   Document processsing jobs creates and stores document metadata in a BigQuery table. Document metadata is required by Agent Builder for indexing the documents. Document metadata contains the uri to the documents stored in the "process" bucket in Google Cloud Storage.
1. **Create and store processed documents in Cloud Storage Bucket for Search and Summarization:**
   The processed documents and document metadata files are also stored in the "process" bucket in Google Cloud Storage for search and summarization.
1. **Data Serving:**
   The processed and stored content from the "process" bucket is imported and indexed in Agent Builder’s BigQuery Data Store.
1. **Powering Search Applications:**
   The extracted data stored in Agent Builder’s BigQuery Data Store is used to power search applications built with Vertex AI Agent Builder.
1. **Business User Access:**
   Business Operations (Biz Ops) employees can access and interact with the processed data through a dedicated Web UI deployed in Cloud Run. This UI leverages search and summarization capabilities of the Vertex AI Agent Builder.
