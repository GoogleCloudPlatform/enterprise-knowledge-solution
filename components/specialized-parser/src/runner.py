import csv
import json
import os
import re
import uuid
from collections import namedtuple
from dataclasses import dataclass, asdict
from typing import List, Dict
from typing import Tuple

import sqlalchemy
import pg8000
from google.api_core.client_info import ClientInfo
from google.api_core.client_options import ClientOptions
from google.api_core.exceptions import GoogleAPICallError, RetryError
from google.api_core.gapic_v1.client_info import ClientInfo
from google.api_core.operation import Operation
from google.cloud import bigquery
from google.cloud import documentai, storage
from google.cloud.alloydb.connector import Connector, IPTypes
from google.cloud.documentai_v1 import BatchProcessMetadata
from google.cloud.exceptions import InternalServerError
from sqlalchemy.engine import Engine

from configs import ProcessorConfig, AlloyDBConfig, JobConfig, BigQueryConfig

FilenamesPair = namedtuple("FilenamesPair", "original_filename txt_filename")


PROCESSED_DOCUMENTS_TABLE_NAME = "eks.processed_documents"


@dataclass
class ProcessedDocument:
    id: str
    original_filename: str
    results_file: str
    run_id: str
    entities: str


USER_AGENT = "cloud-solutions/eks-docai-v1"



class SpecializedParserJobRunner:
    def __init__(
        self,
        job_config: JobConfig,
        processor_config: ProcessorConfig,
        alloydb_config: AlloyDBConfig,
        bigquery_config: BigQueryConfig,
    ):
        self.job_config = job_config
        self.processor_config = processor_config
        self.alloydb_config = alloydb_config
        self.bigquery_config = bigquery_config

        self.alloydb_connection_pool = self.create_connection_pool(alloydb_config)
        self.storage_client = storage.Client(client_info=ClientInfo(user_agent=USER_AGENT))
        self.bq_client = bigquery.Client(client_info=ClientInfo(user_agent=USER_AGENT))

    def run(self):
        print("Verifying AlloyDB output table")
        self.verify_alloydb_table()
        print("Starting Batch Processor operation")
        batch_operation = self.call_batch_processor()
        print("Waiting for Batch operation to finish")
        individual_process_statuses = self.wait_for_completion_and_verify_success(
            batch_operation
        )
        print(f"Parsing results from {self.job_config.gcs_output_uri}")
        parsed_results, filename_pairs = self.read_and_parse_batch_results(
            individual_process_statuses,
        )

        print("Writing metadata to bigquery")
        self.write_metadata_to_bigquery(filename_pairs)
        if not parsed_results:
            print("No parsed results from processor - only metadata")
        else:
            print("Writing results to GCS")
            bucket_name, csv_blob_name = self.write_results_to_gcs(parsed_results)
            print("Writing results to AlloyDB")
            self.write_results_to_alloydb_with_inserts(parsed_results)
            print("Writing results to BigQuery")
            self.write_results_to_bigquery(bucket_name, csv_blob_name)
        print("Done")

    @staticmethod
    def create_connection_pool(alloydb_config: AlloyDBConfig, refresh_strategy: str = "lazy") ->  Engine:
        connector = Connector(refresh_strategy=refresh_strategy)

        def getconn() -> pg8000.dbapi.Connection:  # pyright: ignore [reportAttributeAccessIssue]
            conn = connector.connect(
                instance_uri=alloydb_config.primary_instance,
                driver="pg8000",
                db=alloydb_config.database,
                enable_iam_auth=True,
                user=os.environ["ALLOYDB_USER"],
                ip_type=IPTypes.PRIVATE,
            )
            return conn

        # Not sure why the return type is reported to be MockConnection, when all documentation points for it to be of
        # type Engine. Suppressing error of assignment type, for the moment.
        engine: Engine = sqlalchemy.create_engine(  # pyright: ignore [reportAssignmentType]
            "postgresql+pg8000://",
            creator=getconn,
        )

        engine.dialect.description_encoding = None
        return engine

    def verify_alloydb_table(self) -> None:
        """
        Verify AlloyDB table exists to save results from the processor.
        """
        user = os.environ["ALLOYDB_USER"]
        with self.alloydb_connection_pool.connect() as db_conn:
            db_conn.execute("CREATE SCHEMA IF NOT EXISTS eks")
            db_conn.execute(f'GRANT ALL ON SCHEMA eks TO "{user}"')
            db_conn.execute(f'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA eks TO "{user}"')
            db_conn.execute(f'GRANT USAGE ON SCHEMA eks TO "{user}"')
            db_conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {PROCESSED_DOCUMENTS_TABLE_NAME} (
                id VARCHAR (255) NOT NULL PRIMARY KEY,
                original_filename VARCHAR (2048) NOT NULL,
                results_file VARCHAR (2048) NOT NULL,
                run_id VARCHAR (255) NULL,
                entities JSONB NULL
            )
            """)

    def call_batch_processor(self) -> Operation:
        opts = ClientOptions(api_endpoint=f"{self.processor_config.location}-documentai.googleapis.com")
        client_info = ClientInfo(user_agent=USER_AGENT)
        client = documentai.DocumentProcessorServiceClient(
            client_options=opts, client_info=client_info
        )

        gcs_prefix = documentai.GcsPrefix(gcs_uri_prefix=self.job_config.gcs_input_prefix)
        input_config = documentai.BatchDocumentsInputConfig(gcs_prefix=gcs_prefix)

        gcs_output_config = documentai.DocumentOutputConfig.GcsOutputConfig(
            gcs_uri=self.job_config.gcs_output_uri
        )
        output_config = documentai.DocumentOutputConfig(gcs_output_config=gcs_output_config)

        processor_name = client.processor_path(
            self.processor_config.project,
            self.processor_config.location,
            self.processor_config.processor_id
        )
        request = documentai.BatchProcessRequest(
            name=processor_name,
            input_documents=input_config,
            document_output_config=output_config,
        )
        operation: Operation = client.batch_process_documents(request)
        print(f"Started batch process; {operation.metadata=};")
        return operation

    def wait_for_completion_and_verify_success(self, batch_operation: Operation) -> List[BatchProcessMetadata.IndividualProcessStatus]:
        try:
            print(
                f"Waiting for operation {batch_operation.operation.name} to complete..."
            )
            batch_operation.result(timeout=self.processor_config.timeout)
        # Catch exception when operation doesn't finish before timeout
        except (RetryError, InternalServerError, GoogleAPICallError) as e:
            print(e.message)
            raise e
        print("Batch Process Finished. Checking Status")
        metadata = documentai.BatchProcessMetadata(batch_operation.metadata)

        if metadata.state != documentai.BatchProcessMetadata.State.SUCCEEDED:
            raise ValueError(f"Batch Process Failed: {metadata.state_message}")
        print("Batch process has succeeded")

        return list(metadata.individual_process_statuses)

    def read_and_parse_batch_results(self, individual_process_statuses: List[
        BatchProcessMetadata.IndividualProcessStatus]) -> Tuple[List[ProcessedDocument], List[FilenamesPair]]:
        output_documents: Dict[str, ProcessedDocument] = {}
        output_pairs: List[FilenamesPair] = []
        for process in individual_process_statuses:
            matches = re.match(r"gs://(.*?)/(.*)", process.output_gcs_destination)
            if not matches:
                print(
                    "Could not parse output GCS destination:",
                    process.output_gcs_destination,
                )
                continue

            # Get List of Document Objects from the Output Bucket
            output_bucket, output_prefix = matches.groups()
            output_blobs = self.storage_client.list_blobs(output_bucket, prefix=output_prefix)
            txt_bucket = self.storage_client.bucket(output_bucket)
            for blob in output_blobs:
                # Document AI should only output JSON files to GCS
                if blob.name in output_documents:
                    print(f"Already parsed {blob.name}. Skipping.")
                    continue
                if blob.content_type != "application/json":
                    print(
                        f"Skipping non-supported file: {blob.name} - Mimetype: {blob.content_type}"
                    )
                    continue

                # Read the text recognition output from the processor and create a BQ table row
                document = documentai.Document.from_json(
                    blob.download_as_bytes(),
                    ignore_unknown_fields=True,
                )

                original_filename = (blob.name.rsplit("-", 1)[0]).rsplit("/", 1)[1]
                original_file_path = f"{self.job_config.gcs_input_prefix}/{original_filename}.pdf"
                txt_filename = blob.name.replace(".json", ".txt")
                txt_blob = txt_bucket.blob(txt_filename)
                txt_blob.upload_from_string(document.text)
                txt_file_path = f"gs://{output_bucket}/{txt_filename}"
                print(f"Text file {txt_file_path} created successfully")
                output_pairs.append(FilenamesPair(original_filename=original_file_path, txt_filename=txt_file_path))
                if document.entities:
                    # Since json.dumps(document.entities, indent=None) throws an error ("TypeError: Object of type
                    # RepeatedComposite is not JSON serializable")
                    # We will convert the document to dict, and then use the entities key
                    entities = documentai.Document.to_dict(document)["entities"]  # pyright: ignore [reportIndexIssue]
                    id = str(uuid.uuid4())
                    output_documents[blob.name] = ProcessedDocument(
                        id=id,
                        original_filename=original_file_path,
                        run_id=self.job_config.run_id,
                        results_file=f"gs://{output_bucket}/{blob.name}",
                        entities=json.dumps(entities, indent=None)
                    )

        return list(output_documents.values()), output_pairs

    def write_results_to_gcs(self, parsed_results: List[ProcessedDocument]) -> Tuple[str, str]:
        bucket_name, output_folder = self.get_bucket_name(self.job_config.gcs_output_uri)
        bucket = self.storage_client.get_bucket(bucket_name)
        blob = bucket.blob(f"{output_folder}/processor_results.csv")
        data_dicts = [asdict(d) for d in parsed_results]
        with blob.open("w") as f:
            # not sure why pyright detects `f` as an invalid argument type for csv.DictWriter as an error - this actually works
            writer = csv.DictWriter(
                f,  # pyright: ignore [reportArgumentType]
                fieldnames=data_dicts[0].keys()
            )
            writer.writeheader()
            writer.writerows(data_dicts)

        return bucket_name, str(blob.name)

    @staticmethod
    def get_bucket_name(gcs_uri: str) -> Tuple[str, str]:
        match = re.search(r"gs://([^/]+)/(.*)", gcs_uri)

        if match:
            bucket_name = match.group(1)
            output_folder = match.group(2)
            print(f"{bucket_name=}; {output_folder=}")
            return bucket_name, output_folder
        else:
            print("No bucket name found in the given string.")
            raise ValueError(f"Could not extract bucket from {gcs_uri}")

    def divide_chunks(self, l, n):
        # looping till length l
        for i in range(0, len(l), n):
            yield l[i:i + n]

    def write_results_to_alloydb_with_inserts(self, parsed_results: List[ProcessedDocument]):
        print(
            f"Inserting data to AlloyDB; ({len(parsed_results)} rows)"
        )
        with self.alloydb_connection_pool.connect() as conn:
            for chunk in self.divide_chunks(parsed_results, 50):
                rows = [f"('{x.id}', '{x.original_filename}', '{x.results_file}', '{x.run_id}', '{x.entities}')" for x in
                        chunk]

                sql = f"""
                    INSERT INTO {PROCESSED_DOCUMENTS_TABLE_NAME}
                    VALUES
                    {",".join(rows)}
                """
                conn.execute(sql)

    def write_results_to_alloydb(self, local_filename: str):
        print(
            f"Copying data to AlloyDB table from CSV {local_filename}"
        )
        with self.alloydb_connection_pool.connect() as conn:
            sql = f"""
                COPY {PROCESSED_DOCUMENTS_TABLE_NAME}
                FROM '{local_filename}'
                WITH (
                    FORMAT CSV,
                    HEADER true
                )
            """
            conn.execute(sql)

    def write_results_to_bigquery(self, bucket_name: str, csv_blob_name: str):
        # Construct the full table ID.
        table_ref = (
            self.bq_client
            .get_dataset(f"{os.environ['PROCESSED_DOCS_BQ_PROJECT']}.{os.environ['PROCESSED_DOCS_BQ_DATASET']}")
            .table(os.environ["PROCESSED_DOCS_BQ_TABLE"])
        )

        # Configure the load job.
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND",  # Append data to the table
            source_format=bigquery.SourceFormat.CSV,
            autodetect=False,
            skip_leading_rows=1,
            schema=[
                bigquery.SchemaField("id", "STRING"),
                bigquery.SchemaField("original_filename", "STRING"),
                bigquery.SchemaField("results_file", "STRING"),
                bigquery.SchemaField("run_id", "STRING"),
                bigquery.SchemaField("entities", "JSON"),
            ],
        )

        # Construct the URI for the CSV file in GCS.
        uri = f"gs://{bucket_name}/{csv_blob_name}"

        # Create and run the load job.
        load_job = self.bq_client.load_table_from_uri(uri, table_ref, job_config=job_config)
        load_job.result()  # Wait for the job to complete

    def write_metadata_to_bigquery(self, filename_pairs: List[FilenamesPair]):
        bq_rows = [self.build_bq_metadata_row(p) for p in filename_pairs]

        # Make an API request to insert rows into the table
        errors = self.bq_client.insert_rows_json(self.bigquery_config.general_output_table_id, bq_rows)

        if errors:
            raise Exception(f"Encountered errors while inserting rows in BigQuery: {errors}")

        print("New rows have been added in Big Query table.")

    def build_bq_metadata_row(self, pair: FilenamesPair) -> dict:
        """Program that builds metadata for each processed file"""

        # generate unique id
        id = str(uuid.uuid4())

        # build row with metadata
        row = {
            "id": id,
            "jsonData": json.dumps(
                {
                    "objs": [
                        {
                            "uri": pair.txt_filename,
                            "objid": id,
                            "status": "Indexed",
                            "mimetype": "text/plain",
                        },
                        {
                            "uri": pair.original_filename,
                            "objid": "",
                            "status": "",
                            "mimetype": "application/pdf",
                        },
                    ]
                }
            ),
            "content": {"mimeType": "text/plain", "uri": pair.txt_filename},
        }
        return row
