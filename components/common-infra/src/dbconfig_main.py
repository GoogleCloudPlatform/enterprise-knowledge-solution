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
from dataclasses import dataclass

import pg8000
import sqlalchemy
from google.cloud.alloydb.connector import Connector, IPTypes
from sqlalchemy.engine import Engine


@dataclass
class AlloyDBConfig:
    primary_instance: str
    database: str
    user: str


class DbConfigJobRunner:
    def __init__(
        self,
        alloydb_config: AlloyDBConfig,
    ):
        self.alloydb_config = alloydb_config
        self.alloydb_connection_pool = self.create_connection_pool(alloydb_config)

    def run(self):
        logging.info("Creating alloydb schema and granular db permissions")
        self.create_alloydb_schema_and_permissions()

    @staticmethod
    def create_connection_pool(
        alloydb_config: AlloyDBConfig, refresh_strategy: str = "lazy"
    ) -> Engine:
        connector = Connector(refresh_strategy=refresh_strategy)

        def getconn() -> (
            pg8000.dbapi.Connection
        ):  # pyright: ignore [reportAttributeAccessIssue]
            conn = connector.connect(
                instance_uri=alloydb_config.primary_instance,
                driver="pg8000",
                db=alloydb_config.database,
                enable_iam_auth=True,
                user=alloydb_config.user,
                ip_type=IPTypes.PRIVATE,
            )
            return conn

        engine: Engine = (
            sqlalchemy.create_engine(  # pyright: ignore [reportAssignmentType]
                "postgresql+pg8000://",
                creator=getconn,
            )
        )

        engine.dialect.description_encoding = None
        return engine

    def create_alloydb_schema_and_permissions(self) -> None:
        """
        Verify AlloyDB table exists to save results from the processor.
        """
        user_specialized_parser = os.environ["ALLOYDB_USER_SPECIALIZED_PARSER"]
        with self.alloydb_connection_pool.connect() as db_conn:
            db_conn.execute("CREATE SCHEMA IF NOT EXISTS eks")
            db_conn.execute(f'GRANT ALL ON SCHEMA eks TO "{user_specialized_parser}"')
            db_conn.execute(
                f'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA eks TO "{user_specialized_parser}"'
            )
            db_conn.execute(f'GRANT USAGE ON SCHEMA eks TO "{user_specialized_parser}"')

            db_conn.execute("GRANT ALL ON SCHEMA eks TO postgres")
            db_conn.execute(
                "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA eks TO postgres"
            )


def run() -> None:
    runner = DbConfigJobRunner(
        alloydb_config=AlloyDBConfig(
            primary_instance=os.environ["ALLOYDB_INSTANCE"],
            database=os.environ["ALLOYDB_DATABASE"],
            user=os.environ["ALLOYDB_USER"],
        )
    )
    runner.run()


if __name__ == "__main__":
    run()
