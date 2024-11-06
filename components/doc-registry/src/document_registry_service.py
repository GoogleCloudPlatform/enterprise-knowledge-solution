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

import base64
import json
import logging
import os
import sys
from typing import Optional, Sequence

import proto
from google.api_core.client_info import ClientInfo
from google.api_core.gapic_v1.client_info import ClientInfo as GapicClientInfo
from google.cloud import bigquery_storage_v1  # type: ignore[import-untyped]
from google.cloud import bigquery, storage
from google.cloud.bigquery_storage_v1 import types
from google.protobuf import descriptor_pb2


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
    client_info = ClientInfo(user_agent="cloud-solutions/eks-doc-processors-v1")
    gapic_client_info = GapicClientInfo(
        user_agent="cloud-solutions/eks-doc-processors-v1"
    )

    @classmethod
    def get_storage_client(cls):
        if cls.storage_client is None:
            cls.storage_client = storage.Client(client_info=cls.client_info)
        return cls.storage_client

    @classmethod
    def get_bq_client(cls):
        if cls.bq_client is None:
            cls.bq_client = bigquery.Client(client_info=cls.client_info)
        return cls.bq_client

    @classmethod
    def get_bq_write_stream(cls):
        if cls.bq_write_client is None:
            cls.bq_write_client = bigquery_storage_v1.BigQueryWriteClient(
                client_info=cls.gapic_client_info
            )
        return cls.bq_write_client


class RegistryDocument:
    def __init__(self, id: str, bucket: str, folder: str, name: str, crc32: int):
        self.id = id
        self.bucket = bucket
        self.folder = folder
        self.name = name
        self.crc32 = crc32

    def get_json_str(self):
        return json.dumps(self.__dict__)

    def __str__(self):
        return self.get_json_str()

    def get_gcs_name(self):
        return self.name if self.folder == "" else f"{self.folder}/{self.name}"

    def get_gcs_uri(self):
        return r"gs://" + f"{self.bucket}/{self.get_gcs_name()}"


class GCSFolder:

    def __init__(self, full_folder_path: str):
        self.bucket_name, self.folder_prefix = GCSFolder.extract_bucket_and_folder(
            full_folder_path
        )
        self.bucket: Optional[storage.Bucket] = None
        self.docs: Optional[list[RegistryDocument]] = None

    def get_bucket(self):
        if self.bucket is None:
            self.bucket = GoogleCloudClients.get_storage_client().bucket(
                self.bucket_name
            )
        return self.bucket

    def get_documents_in_folder(self):
        if self.docs is None:
            blobs = self.get_bucket().list_blobs(prefix=self.folder_prefix)
            self.docs = [GCSFolder.blob_to_doc(blob) for blob in blobs]
        for doc in self.docs:
            yield doc

    def write_to_folder(self, content: str, file_name: str, mime_type: str):
        blob_name = (
            file_name
            if self.folder_prefix == ""
            else f"{self.folder_prefix}/{file_name}"
        )
        self.get_bucket().blob(blob_name).upload_from_string(
            content, content_type=mime_type
        )

    @staticmethod
    def blob_to_doc(blob: storage.Blob) -> RegistryDocument:
        crc32_int = GCSFolder.base64_to_int(blob.crc32c)
        bucket_name = blob.bucket.name
        folder, doc_name = GCSFolder.extract_folder_doc_name(blob.name)
        return RegistryDocument("", bucket_name, folder, doc_name, crc32_int)

    @staticmethod
    def base64_to_int(base64_str: str) -> int:
        crc32c_bytes = base64.b64decode(base64_str)
        return int.from_bytes(crc32c_bytes, byteorder="big")

    @staticmethod
    def extract_folder_doc_name(blob_name: str):
        """split blob name into folder prefix and file"""
        parts = blob_name.split(r"/")
        doc_name = parts[-1]
        folder = "/".join(parts[:-1])
        return folder, doc_name

    @staticmethod
    def extract_bucket_and_folder(gcs_folder_uri: str):
        parts = gcs_folder_uri.replace(r"gs://", "").split(r"/")
        bucket_name = parts[0]
        folder = "/".join(parts[1:])
        return bucket_name, folder


def look_up_document(registry_table: str, crc32s: list[str]):
    """Given a list of crc32 values and return all the matching entries from the document registry table"""
    unique_crc32s = list(set(crc32s))
    select_crc32_rows = [f"SELECT '{crc32}' AS crc32" for crc32 in unique_crc32s]
    crc32_table = " UNION ALL ".join(select_crc32_rows)
    crc32_table_alias = "crc32_table"
    query = " ".join(
        [
            f"WITH {crc32_table_alias} AS ({crc32_table})",
            f"SELECT id, fileName, gcsUri, a.crc32 FROM {registry_table} AS a",
            f"INNER JOIN {crc32_table_alias} AS b",
            "ON a.crc32 = b.crc32",
        ]
    )
    return GoogleCloudClients.get_bq_client().query(query)


def add_new_documents_to_registry(
    input_table: str, registry_table: str, output_folder: str
):
    """Given a document processing table,
    for each entry insert corresponding entry to document registry table
    including internal id, gcsUri and crc32"""
    query = f"SELECT id, content.uri FROM {input_table}"
    rows = GoogleCloudClients.get_bq_client().query(query)
    if rows.result().total_rows == 0:
        return
    input_folder = GCSFolder(
        extract_common_gcs_folder_from_processing_table(input_table)
    )
    results = input_rows_to_document_info(rows, input_folder)
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
    result_obj = {
        "task": "add-new-documents-to-registry",
        "result": f"Added {len(results)} new document entries from {input_table=}",
    }
    GCSFolder(output_folder).write_to_folder(
        json.dumps(result_obj), "result.json", "application/json"
    )


def extract_folder_including_bucket_from_blob_uri(blob_uri: str):
    parts = blob_uri.replace(r"gs://", "").split(r"/")
    return "/".join(parts[:-1])


def extract_common_gcs_folder_from_processing_table(processing_table: str):
    """Extrct the common path share by all the document uri:s in the input table"""
    query = f"select max(content.uri) max_uri, min(content.uri) min_uri from {processing_table}"
    rows = GoogleCloudClients.get_bq_client().query(query)
    row = next(rows.result())
    max_uri = extract_folder_including_bucket_from_blob_uri(row.max_uri)
    min_uri = extract_folder_including_bucket_from_blob_uri(row.min_uri)
    i = 0
    while i < len(min_uri) and i < len(max_uri) and max_uri[i] == min_uri[i]:
        i += 1
    return max_uri[:i]


def input_rows_to_document_info(
    rows, input_folder: GCSFolder
) -> Sequence[DocumentInfo]:
    """Convert document processing entries to DocumentInfo object"""
    uri_look_up = {
        doc.get_gcs_uri(): doc for doc in input_folder.get_documents_in_folder()
    }
    result = []
    for row in rows:
        if row.uri in uri_look_up:
            doc = uri_look_up[row.uri]
            result.append(
                DocumentInfo(
                    id=row.id, fileName=doc.name, gcsUri=row.uri, crc32=str(doc.crc32)
                )
            )
    return result


def detect_duplicates(folder_uri: str, registry_table: str):
    """Return all the file that already exist in the document registry"""
    folder_to_check = GCSFolder(folder_uri)
    crc32s = [str(doc.crc32) for doc in folder_to_check.get_documents_in_folder()]
    matches_found = look_up_document(registry_table, crc32s)
    duplicates = []
    match_dict = {row.crc32: row for row in matches_found}
    for doc in folder_to_check.get_documents_in_folder():
        doc_crc32 = str(doc.crc32)
        if doc_crc32 in match_dict:
            duplicates.append(
                {
                    "doc": doc.get_gcs_uri(),
                    "existing_doc": {
                        "uri": match_dict[doc_crc32].gcsUri,
                        "id": match_dict[doc_crc32].id,
                    },
                }
            )
    return duplicates


def run_detect_duplicates(folder_to_check, doc_registry_table, output_folder):
    jsonl_str = "\n".join(
        [
            json.dumps(dup)
            for dup in detect_duplicates(folder_to_check, doc_registry_table)
        ]
    )
    GCSFolder(output_folder).write_to_folder(
        jsonl_str, "result.jsonl", "application/jsonl"
    )


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
        proto_descriptor = descriptor_pb2.DescriptorProto()  # pylint: disable=no-member
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


if __name__ == "__main__":
    # Retrieve Job-defined env vars
    TASK_INDEX = os.getenv("CLOUD_RUN_TASK_INDEX", 0)
    TASK_ATTEMPT = os.getenv("CLOUD_RUN_TASK_ATTEMPT", 0)

    # Retrieve User-defined env vars
    GCS_INPUT_FILE_BUCKET = os.getenv("GCS_INPUT_FILE_BUCKET")
    GCS_IO_URI = os.getenv("GCS_IO_URI")
    BQ_DOC_REGISTRY_TABLE = os.getenv("BQ_DOC_REGISTRY_TABLE")
    ADD_DOCS = os.getenv("ADD_DOCS", "False").lower() in ("true", "1", "t")
    BQ_INGESTED_DOC_TABLE = os.getenv("BQ_INGESTED_DOC_TABLE")

    if not BQ_DOC_REGISTRY_TABLE or not GCS_IO_URI:
        message = (
            f"Environment variables missing; "
            f"{BQ_DOC_REGISTRY_TABLE=}, "
            f"{GCS_IO_URI=}, "
        )
        logging.error(message)
        sys.exit(1)
    if not ADD_DOCS and not GCS_INPUT_FILE_BUCKET:
        message = f"Environment variables missing; " f"{GCS_INPUT_FILE_BUCKET=}, "
        logging.error(message)
        sys.exit(1)
    if ADD_DOCS and not BQ_INGESTED_DOC_TABLE:
        message = f"Environment variables missing; " f"{BQ_INGESTED_DOC_TABLE=}, "
        logging.error(message)
        sys.exit(1)
    try:
        logging.info(f"Starting Task #{TASK_INDEX} (att. {TASK_ATTEMPT}.")
        if not ADD_DOCS:
            logging.info(f"{GCS_INPUT_FILE_BUCKET=}, " f"{BQ_DOC_REGISTRY_TABLE=}, ")
            run_detect_duplicates(
                GCS_INPUT_FILE_BUCKET, BQ_DOC_REGISTRY_TABLE, GCS_IO_URI
            )
        else:
            logging.info(f"{BQ_INGESTED_DOC_TABLE=}, " f"{BQ_DOC_REGISTRY_TABLE=}, ")
            add_new_documents_to_registry(
                BQ_INGESTED_DOC_TABLE, BQ_DOC_REGISTRY_TABLE, GCS_IO_URI # type: ignore
            )
        logging.info(f"Completed Task #{TASK_INDEX} (att. {TASK_ATTEMPT}.")
    except Exception as e:
        logging.error(f"Task Index {TASK_INDEX} (att. {TASK_ATTEMPT} failed!" f"{e}")
        sys.exit(1)
