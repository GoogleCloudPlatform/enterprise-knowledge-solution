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

import logging.config
import logging.handlers
import os
import re
from dataclasses import dataclass

from google.api_core.client_info import ClientInfo as bg_ClientInfo
from google.api_core.gapic_v1.client_info import ClientInfo
from typing import Optional, List

import sqlalchemy
from google.cloud import bigquery, storage, discoveryengine, discoveryengine_v1
from google.cloud.alloydb.connector import Connector, IPTypes

logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "[%(levelname)s|%(module)s|L%(lineno)d] %(asctime)s: %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "simple",
            "stream": "ext://sys.stdout",
        }
    },
    "loggers": {
        "root": {
            "level": "DEBUG",
            "handlers": [
                "console",
            ],
        }
    },
}

logging.config.dictConfig(logging_config)
logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)


# helper function to return SQLAlchemy connection pool
def init_connection_pool(connector: Connector) -> sqlalchemy.engine.Engine:
    # function used to generate database connection
    def getconn():
        conn = connector.connect(
            instance_uri=os.environ["ALLOYDB_INSTANCE"],
            driver="pg8000",
            db=os.environ["ALLOYDB_DATABASE"],
            enable_iam_auth=True,
            user=os.environ["ALLOYDB_USER_CONFIG"],
            ip_type=IPTypes.PRIVATE,
        )
        return conn

    # create connection pool
    pool = sqlalchemy.create_engine(
        "postgresql+pg8000://",
        creator=getconn,
    )
    return pool

USER_AGENT = "cloud-solutions/eks-docai-v1"

@dataclass
class DocProcessingRecord:
    id: str
    gcs_uris: List[str]
    obj_ids: List[str]
    results_files: List[str]

@dataclass
class DataStoreConfig:
    project_id: str
    region: str
    collection: str
    id: str
    branch: str

def get_docs_data_from_bq(
    bq_client: bigquery.Client,
    bq_data_table: str,
    doc_id: Optional[str]
) -> List[DocProcessingRecord]:

    where_clause = f"WHERE dp.id = '{doc_id}'" if doc_id else ""
    sql = f"""
    SELECT
        dp.id,
        ARRAY_AGG(DISTINCT JSON_EXTRACT_SCALAR(objs, "$.uri")) AS gcs_uris,
        ARRAY_AGG(DISTINCT JSON_EXTRACT_SCALAR(objs, "$.objid")) AS obj_ids,
        ARRAY_AGG(DISTINCT pd.results_file IGNORE NULLS) AS results_files
    FROM `{bq_data_table}` AS dp
    CROSS JOIN UNNEST(JSON_EXTRACT_ARRAY(PARSE_JSON(jsonData), "$.objs")) AS objs
    LEFT JOIN `docs_store.prcessed_documents` AS pd ON dp.id = pd.id
    {where_clause}
    GROUP BY dp.id;
    """
    res = bq_client.query(sql)
    if res.errors:
        raise Exception(res.errors[0]["message"])
    return [DocProcessingRecord(
        id=row["id"],
        gcs_uris=row["gcs_uris"],
        obj_ids=row["obj_ids"],
        results_files=row["results_files"]) for row in res.result()]


def delete_doc_from_agent_build(
    document_service_client: discoveryengine.DocumentServiceClient,
    data_store_config: DataStoreConfig,
    obj_id: str
):
    full_doc_id = \
            f"projects/{data_store_config.project_id}" \
            f"/locations/{data_store_config.region}" \
            f"/collections/{data_store_config.collection}" \
            f"/dataStores/{data_store_config.id}" \
            f"/branches/{data_store_config.branch}" \
            f"/documents/{obj_id}"

    logger.info(f"Deleting document {full_doc_id}")

    request = discoveryengine_v1.DeleteDocumentRequest(
        name=full_doc_id
    )

    document_service_client.delete_document(request=request)


def delete_doc_from_bq_processed_documents(bq_client: bigquery.Client, doc_id: str):
    sql = f"DELETE FROM docs_store.prcessed_documents WHERE id='{doc_id}'"
    logger.info(f"Deleting document {doc_id} from processed documents table")
    res = bq_client.query(sql)
    if res.errors:
        raise Exception(res.errors[0]["message"])


def delete_doc_from_alloydb_processed_documents(doc_id: str):
    # Delete data from AlloyDB
    logger.info(f"Deleting document {doc_id} from AlloyDB")
    with Connector(refresh_strategy="lazy") as connector:
        pool = init_connection_pool(connector)
        with pool.connect() as db_conn:
            db_conn.execute(
                sqlalchemy.text(
                    f"DELETE FROM eks.prcessed_documents WHERE id='{doc_id}'"
                )
            )


def delete_doc_from_gcs(storage_client: storage.Client, gcs_uri: str):
    matches = re.match(r"gs://(.*?)/(.*)", gcs_uri)
    if not matches:
        raise Exception(f"Could not parse output GCS destination: {gcs_uri}")
    # Get List of Document Objects from the Output Bucket
    gcs_bucket, gcs_path = matches.groups()
    logger.info(f"Deleting document {gcs_path} from GCS bucket {gcs_bucket}")
    bucket = storage_client.bucket(gcs_bucket)
    bucket.blob(gcs_path).delete()


def delete_doc_from_metadata_table(bq_client: bigquery.Client, data_table: str, doc_id: str):
    sql = f"DELETE FROM `{data_table}` WHERE id='{doc_id}'"
    logger.info(f"Deleting document {doc_id} from {data_table} table")
    res = bq_client.query(sql)
    if res.errors:
        raise Exception(res.errors[0]["message"])


def delete_doc_from_doc_registry(bq_client: bigquery.Client, doc_id: str):
    sql = f"DELETE FROM `docs_registry.docs_registry` WHERE id='{doc_id}'"
    logger.info(f"Deleting document {doc_id} from document registry table")
    res = bq_client.query(sql)
    if res.errors:
        raise Exception(res.errors[0]["message"])


def drop_data_table(bq_client: bigquery.Client, data_table: str):
    logger.info(f"Dropping table {data_table} due to batch mode. Verifying table is empty.")
    res = bq_client.query(f"SELECT COUNT(*) AS row_count FROM {data_table}")
    if res.errors:
        raise Exception(res.errors[0]["message"])
    row_count = [row[0]["row_count"] for row in res.result()][0]
    if row_count > 0:
        raise Exception(f"Something went wrong. Table is not empty. Still contains {row_count} rows")
    logger.info(f"Table {data_table} is empty. Proceeding to drop it.")
    res = bq_client.query(f"DROP TABLE {data_table}")
    if res.errors:
        raise Exception(res.errors[0]["message"])


def main(
    data_store_config: DataStoreConfig,
    run_id: str,
    mode: str,
    doc_id: Optional[str] = None,
):
    storage_client = storage.Client(
        client_info=ClientInfo(user_agent=USER_AGENT)
    )
    bq_client = bigquery.Client(
        client_info=bg_ClientInfo(user_agent=USER_AGENT)
    )
    document_service_client = discoveryengine.DocumentServiceClient(
        client_options={"api_endpoint": f"{data_store_config.region}-documentai.googleapis.com"},
        client_info=ClientInfo(user_agent=USER_AGENT)
    )
    data_table = f"docs_store.docs_processing_{run_id.replace('-', '_')}"
    docs = get_docs_data_from_bq(bq_client, data_table, doc_id)
    logger.info(f"Deleting {len(docs)} documents")
    for doc in docs:
        logger.info(f"Deleting document {doc.id} with URIs: {doc.gcs_uris}")
        for obj_id in doc.obj_ids:
            delete_doc_from_agent_build(document_service_client, data_store_config, obj_id)
        delete_doc_from_bq_processed_documents(bq_client, doc.id)
        delete_doc_from_alloydb_processed_documents(doc.id)
        for gcs_uri in doc.gcs_uris + doc.results_files:
            delete_doc_from_gcs(storage_client, gcs_uri)
        delete_doc_from_metadata_table(bq_client, data_table, doc.id)
        delete_doc_from_doc_registry(bq_client, doc.id)
    if mode == "batch":
        drop_data_table(bq_client, data_table)

if __name__ == "__main__":
    _data_store_config = DataStoreConfig(
        project_id=os.environ["DATA_STORE_PROJECT_ID"],
        region=os.environ["DATA_STORE_REGION"],
        collection=os.environ["DATA_STORE_COLLECTION"],
        id=os.environ["DATA_STORE_ID"],
        branch=os.environ["DATA_STORE_BRANCH"],
    )
    _run_id = os.environ["RUN_ID"]
    _mode = os.environ["MODE"]
    assert _mode in ["single", "batch"], "Mode must be either 'single' or 'batch'"
    _doc_id = os.environ.get("DOC_ID")  # optional, hence `get` method
    assert (_mode == "batch" and _doc_id is None) or (_mode == "single" and _doc_id is not None), \
        "Mode and doc_id mismatch"

    main(_data_store_config, _run_id, _mode, _doc_id)
