# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
import sys
import proto
import json
from typing import Optional
from google.cloud import storage, bigquery
from google.api_core.client_info import ClientInfo
from google.api_core.gapic_v1.client_info import ClientInfo
from google.cloud.bigquery_storage_v1 import types
from google.protobuf import descriptor_pb2
from typing import Sequence

from google.cloud import bigquery_storage_v1  # type: ignore[import-untyped]
import base64

class DocumentInfo(proto.Message):
    """DocumentInfo for a file ingested in EKS"""
    id = proto.Field(proto.STRING, number=1)
    fileName = proto.Field(proto.STRING, number=2)
    gcsUri = proto.Field(proto.STRING, number=3)
    crc32 = proto.Field(proto.STRING, number=4)

class GoogleCloudClients:
    storage_client: Optional[storage.Client] = None
    bq_client: Optional[bigquery.Client] = None
    bq_write_client: Optional[bigquery_storage_v1.BigQueryWriteClient] = None
    client_info = ClientInfo(
        user_agent="cloud-solutions/eks-doc-processors-v1"
    )

    @classmethod
    def get_storage_client(cls):
        if cls.storage_client is None:
            cls.storage_client = storage.Client(
                client_info=cls.client_info
            )
        return cls.storage_client
    
    @classmethod
    def get_bq_client(cls):
        if cls.bq_client is None:
            cls.bq_client = bigquery.Client(
                client_info=cls.client_info
            )
        return cls.bq_client
    
    @classmethod
    def get_bq_write_stream(cls):
        if cls.bq_write_client is None:
            cls.bq_write_client = bigquery_storage_v1.BigQueryWriteClient(
                client_info=cls.client_info
            )
        return cls.bq_write_client
        

def open_bucket(bucket_name: str):
    """Open a bucket."""    
    return GoogleCloudClients.get_storage_client().bucket(bucket_name)  # pyright: ignore

def get_blob_crc32_in(blob_list: list[storage.Blob]):
    """Extract crc32c from a list of blob, also convert from base64 to int"""
    return [base64_to_int(blob.crc32c) for blob in blob_list]

def look_up_document(registry_table: str, crc32s: list[int]):
    """Given a list of crc32 values and return all the matching entries from the document registry table"""
    unique_crc32s = list(set(crc32s))
    select_crc32_rows = [f"SELECT '{crc32}' AS crc32" for crc32 in unique_crc32s]
    crc32_table = " UNION ALL ".join(select_crc32_rows)
    crc32_table_alias = "crc32_table"
    query = " ".join([
        f"WITH {crc32_table_alias} AS ({crc32_table})",
        f"SELECT id, fileName, gcsUri, a.crc32 FROM {registry_table} AS a",
        f"INNER JOIN {crc32_table_alias} AS b",
        f"ON a.crc32 = b.crc32"
    ])
    return GoogleCloudClients.get_bq_client().query(query)


def add_new_documents_to_registry(input_table: str, registry_table: str):
    """Given a document processing table, 
    for each entry insert corresponding entry to document registry table 
    including internal id, gcsUri and crc32"""
    query = f"SELECT id, content.uri FROM {input_table}"
    rows = GoogleCloudClients.get_bq_client().query(query)
    results = [input_row_to_document_info(row) for row in rows]
    if len(results) == 0:
        return
    
    ref = bigquery.TableReference.from_string(registry_table)
    path = GoogleCloudClients.get_bq_write_stream().write_stream_path(
        project=ref.project,
        dataset=ref.dataset_id,
        table=ref.table_id,
        stream="_default",
    )

    req = types.AppendRowsRequest()
    req.write_stream = path
    req.proto_rows = get_proto_data(results)
    GoogleCloudClients.get_bq_write_stream().append_rows(requests=iter([req]))


def input_row_to_document_info(row):
    """Convert single document processing entry to DocumentInfo object"""
    bucket_name, blob_name, file_name = extract_bucket_and_blob_name(row)
    bucket = open_bucket(bucket_name)
    blob = bucket.get_blob(blob_name)
    return DocumentInfo(
        id=row.id,
        fileName=file_name,
        gcsUri=row.uri,
        crc32=str(base64_to_int(blob.crc32c))
    )
    

def detect_duplicates(folder_uri: str, registry_table: str):
    """Return all the file that already exist in the document registry"""
    bucket_name, folder = extract_bucket_and_folder(folder_uri)
    bucket_to_check = open_bucket(bucket_name)
    matches_found = look_up_document(registry_table, get_blob_crc32_in(bucket_to_check.list_blobs(prefix=folder)))
    duplicates = []
    match_dict = {row.crc32: row for row in matches_found}
    for doc in bucket_to_check.list_blobs():
        doc_crc32 = str(base64_to_int(doc.crc32c))
        if doc_crc32 in match_dict:
            duplicates.append(
                {
                    'doc': doc.id,
                    'existing_doc': {
                        'uri': match_dict[doc_crc32].gcsUri,
                        'id':  match_dict[doc_crc32].id
                    }
                }
            )
    return duplicates


def base64_to_int(base64_str: str):
    crc32c_bytes = base64.b64decode(base64_str) 
    return int.from_bytes(crc32c_bytes, byteorder='big')

def extract_bucket_and_folder(gcs_folder_uri: str):
    parts = gcs_folder_uri.replace(r"gs://", "").split(r"/")
    bucket_name = parts[0]
    folder = "/".join(parts[1:])
    return bucket_name, folder

def extract_bucket_and_blob_name(row):
    """split gcsUri into bucket folder file"""
    uri = row.uri.replace(r"gs://", "")
    parts = uri.split(r"/")
    return parts[0], "/".join(parts[1:]), parts[-1]

def get_proto_data(obj: Sequence[proto.Message], with_schema: bool = True):
    """Convert a sequence of messages into proto data"""

    proto_data = types.AppendRowsRequest.ProtoData()

    # Bring in the schema if requested (required first time)
    if with_schema:
        proto_schema = types.ProtoSchema()
        proto_descriptor = (
            descriptor_pb2.DescriptorProto()
        )  # pylint: disable=no-member
        type(obj[0]).pb().DESCRIPTOR.CopyToProto(proto_descriptor)
        proto_schema.proto_descriptor = proto_descriptor
        proto_data.writer_schema = proto_schema

    # Serialize the rows
    proto_rows = types.ProtoRows()
    for o in obj:
        proto_rows.serialized_rows.append(
            type(o).serialize(o)
        )  # pylint: disable=no-member

    proto_data.rows = proto_rows

    return proto_data

def write_to_bucket(content:str, destination_uri:str, file_name:str, mime_type: str):
    bucket_name, folder = extract_bucket_and_folder(destination_uri)
    bucket = open_bucket(bucket_name)
    blob_name = f"{folder}/{file_name}"
    bucket.blob(blob_name).upload_from_string(
        content, content_type=mime_type
    )


if __name__ == "__main__":
    # Retrieve Job-defined env vars
    TASK_INDEX = os.getenv("CLOUD_RUN_TASK_INDEX", 0)
    TASK_ATTEMPT = os.getenv("CLOUD_RUN_TASK_ATTEMPT", 0)
    
    # Retrieve User-defined env vars
    GCS_INPUT_FILE_BUCKET = os.getenv("GCS_INPUT_FILE_BUCKET")
    GCS_IO_URI = os.getenv("GCS_IO_URI")
    BQ_DOC_REGISTRY_TABLE = os.getenv("BQ_DOC_REGISTRY_TABLE")
    ADD_DOCS = os.getenv("ADD_DOCS", 'False').lower() in ('true', '1', 't')
    BQ_INGESTED_DOC_TABLE = os.getenv("BQ_INGESTED_DOC_TABLE")

    
    if (not BQ_DOC_REGISTRY_TABLE
        or not GCS_IO_URI):
        message = (
            f"Environment variables missing; "
            f"{BQ_DOC_REGISTRY_TABLE=}, "
            f"{GCS_IO_URI=}, "
        )
        logging.error(message)
        sys.exit(1)
    if not ADD_DOCS and not GCS_INPUT_FILE_BUCKET:
        message = (
            f"Environment variables missing; "
            f"{GCS_INPUT_FILE_BUCKET=}, "
        )
        logging.error(message)
        sys.exit(1)
    if ADD_DOCS and not BQ_INGESTED_DOC_TABLE:
        message = (
            f"Environment variables missing; "
            f"{BQ_INGESTED_DOC_TABLE=}, "
        )
        logging.error(message)
        sys.exit(1)
    try:
        logging.info(f"Starting Task #{TASK_INDEX} (att. {TASK_ATTEMPT}.")
        if not ADD_DOCS:
            logging.info(
                f"{GCS_INPUT_FILE_BUCKET=}, "
                f"{BQ_DOC_REGISTRY_TABLE=}, "
            )
            jsonl_str = "\n".join([json.dumps(dup) for dup in detect_duplicates(GCS_INPUT_FILE_BUCKET, BQ_DOC_REGISTRY_TABLE)])
            write_to_bucket(jsonl_str, GCS_IO_URI, "result.jsonl", "application/jsonl")
        else:
            logging.info(
                f"{BQ_INGESTED_DOC_TABLE=}, "
                f"{BQ_DOC_REGISTRY_TABLE=}, "
            )
            add_new_documents_to_registry(BQ_INGESTED_DOC_TABLE, BQ_DOC_REGISTRY_TABLE)
        logging.info(f"Completed Task #{TASK_INDEX} (att. {TASK_ATTEMPT}.")
    except Exception as e:
        logging.error(f"Task Index {TASK_INDEX} (att. {TASK_ATTEMPT} failed!" f"{e}")
        sys.exit(1)

