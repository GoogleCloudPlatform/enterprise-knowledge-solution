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
import sqlalchemy
from sqlalchemy.engine import Engine
from google.cloud.alloydb.connector import Connector

def verify_alloydb_table(alloydb_connection: Engine) -> None:
    """
    Verify AlloyDB table exists to save results from the processor.
    Args:
        alloydb_connection: Connection pool to open to the alloydb instance.

    Returns:
        None
    """
    with alloydb_connection.connect() as db_conn:
        db_conn.execute("""
            CREATE TABLE IF NOT EXISTS `parsed_invoice_data` (
                results_file VARCHAR(2048) NOT NULL,
                original_filename VARCHAR(2048) NOT NULL,
                entity_type VARCHAR(2048),
                raw_text TEXT,
                normalized_text TEXT,
                confidence REAL NOT NULL DEFAULT 0,
                run_id VARCHAR(256)
            )
        """)


def create_alloydb_connection_pool(
    alloydb_project: str,
    alloydb_location: str,
    alloydb_cluster: str,
    alloydb_instance: str,
    alloydb_database: str
) -> Engine:
    """
    Create a connection pool to the AlloyDB instance.
    Args:
        alloydb_project: Project of the AlloyDB instance
        alloydb_location: Location of the AlloyDB instance
        alloydb_cluster: Cluster name of the AlloyDB instance
        alloydb_instance: Name of the AlloyDB instance
        alloydb_database: Database to use for results table.

    Returns:
        Connection pool
    """
    connector = Connector()

    def getconn():
        conn = connector.connect(
            f"projects/{alloydb_project}/locations/{alloydb_location}/clusters/{alloydb_cluster}/inst"
            f"ances/{alloydb_instance}",
            "pg8000",
            db=alloydb_database,
        )
        return conn

    # Not sure why the return type is reported to be MockConnection, when all documentation points for it to be of
    # type Engine. Suppressing error of assignment type, for the moment.
    pool: Engine = sqlalchemy.create_engine(  # pyright: ignore [reportAssignmentType]
        "postgresql+pg8000://",
        creator=getconn,
    )
    return pool

def write_results_to_alloydb(bucket_name: str, csv_blob_name: str, alloydb_connection: Engine):
    """

    Args:
        bucket_name:
        csv_blob_name:
        alloydb_connection:

    Returns:

    """
    logging.info(f"Copying data to AlloyDB table from CSV gs://{bucket_name}/{csv_blob_name}")
    with alloydb_connection.connect() as conn:
        sql = f"""
            COPY `parsed_invoice_data`
            FROM 'gs://{bucket_name}/{csv_blob_name}'
            WITH (
                FROMAT CSV,
                HEADER true
            )
        """
        conn.execute(sql)

