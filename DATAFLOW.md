# Enterprise Knowledge Solution Dataflow

1. **Upload documents and trigger document processing workflow:**
   The [uploader persona](docs/access_control.md) uploads documents (Excel, PDF, Word, Text, Outlook, Zip) to a designated "input" bucket in Google Cloud Storage. This persona might be an employee responsible for manually curating and uploading the content, or it might be an automated cron job that transfers documents from a source system.

1. **Validate the documents:**
   Documents that fail validation (unsupported file type, duplicate files, or too large) are redirected to a separate "reject" bucket within Google Cloud Storage for further review and handling.

1. **Initiate the processing jobs:**
   The workflow initiates specific processing jobs based on the document type:

   - `Document Classifier (Cloud Run -> Doc AI Custom Classifier):` Identify PDF document type (Any form, bank statements, invoices, pay slip, lending doc and utility bills)
   - `Specialized Parser (Cloud Run -> Doc AI Form and Specialied Parser):` Processes forms and documents (Any form, bank statements, invoices, pay slip, lending doc and utility bills)
   - `MS Office Document Processor (Cloud Run):` Prepare Outlook, Excel and ZIP files for Search and Summarization.

1. **Utilize Document AI Batch API:**
   The Specialized Parser Job leverages Document AI Batch API for asynchronous processing of large document volumes. Extract data from forms and documents (any form, bank statements, invoices, pay slip, lending doc and utility bills) using Document AI.

1. **Store data extracted from PDF forms in AlloyDB and BigQuery:**
   The data extracted from the PDF forms and documents using Document AI is stored in AlloyDB and BigQuery.
   The Specialized Parser Job uses Document AI Batch API to extract data elements from the documents and stores the extracted data elements in AlloyDB, BigQuery and Firestore.

1. **Create and store document metadata in BigQuery for search and summarization:**
   Document processsing jobs creates and stores document metadata in a BigQuery table. Document metadata is required by Agent Builder for indexing the documents. Document metadata contains the URI to the documents stored in the "process" bucket in Google Cloud Storage.

1. **Prepare and store document content for indexing:**
   Each processor extracts content and structured data from the documents. The extracted content (PDF, docx, txt) is stored in a “process” bucket within Google Cloud Storage.

1. **Index documents for search and summarization:**
   The unstructured documents from the “process bucket” and document metadata from BigQuery are imported and indexed in Agent Builder’s BigQuery Data Store.

1. **Index structed data for search and summarization :**
   The data extracted from unstructred documents is imported into Agent Builder AlloyDB Data Store.

1. **Serve data to the search application:**
   The content and the extracted data stored in Agent Builder Data Stores is used to power search and converstational Agents(Apps) built with Vertex AI Agent Builder.

1. **Access the search application:**
   The [reader persona](docs/access_control.md) can access and interact with the processed data through a dedicated Web UI deployed in Cloud Run. This UI leverages search and summarization capabilities of the Vertex AI Agent Builder.

1. **Render structured data on Web-UI:**
   Data extracted from unstructured documents using ML models (Document AI) may not be accurate. It requires a human-in-the-loop (HITL) for validation and correction of the extracted data. The Web UI displays the data for human validation and correction.
