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
""""BigQueryWriter for storage writes into a BigQuery table"""

import functools
import logging
from typing import Sequence

import proto
from google.api_core.gapic_v1.client_info import ClientInfo
from google.cloud import bigquery_storage_v1  # type: ignore[import-untyped]
from google.cloud.bigquery import TableReference
from google.cloud.bigquery_storage_v1 import types  # type: ignore[import-untyped]
from google.protobuf import descriptor_pb2

__protobuf__ = proto.module(package="")

logger = logging.getLogger(__name__)


class DocumentMetadata(proto.Message):
    """DocumentMetadata for Agent Builder"""

    id = proto.Field(proto.STRING, number=1)
    jsonData = proto.Field(proto.STRING, number=2)

    class Content(proto.Message):
        """Content reference for Agent Builder"""

        mimeType = proto.Field(proto.STRING, number=1)
        uri = proto.Field(proto.STRING, number=2)

    content = proto.Field(Content, number=3)


class BigQueryWriter:
    """BigQueryWriter - using storage API streaming to insert new records"""

    @staticmethod
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

    def __init__(self, table: str):
        ref = TableReference.from_string(table)
        self.client = bigquery_storage_v1.BigQueryWriteClient(
            client_info=ClientInfo(
                user_agent="cloud-solutions/eks-doc-processors-v1",
            )
        )
        self.path = self.client.write_stream_path(
            project=ref.project,
            dataset=ref.dataset_id,
            table=ref.table_id,
            stream="_default",
        )

    def write_results(self, results: Sequence[DocumentMetadata]):
        """Write some results to the table"""

        if len(results) == 0:
            return

        req = types.AppendRowsRequest()
        req.write_stream = self.path
        req.proto_rows = BigQueryWriter.get_proto_data(results)

        logger.debug(
            "Uploading to BigQuery URIs %s",
            ", ".join([r.content.uri for r in results]),  # pyright: ignore
        )
        self.client.append_rows(requests=iter([req]))


@functools.cache
def get_bq_writer(table: str = ""):
    """Create writer for a table"""

    if table == "":
        return None

    return BigQueryWriter(table)
