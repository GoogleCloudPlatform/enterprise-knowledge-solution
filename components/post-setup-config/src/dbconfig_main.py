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

import sqlalchemy
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


users = [
    os.environ["ALLOYDB_USER_CONFIG"],
    "postgres",
] + os.environ[
    "ALLOYDB_USERS"
].split(",")


logger.info("Setting up for eks.")
# Create role if not exists
with Connector(refresh_strategy="lazy") as connector:
    pool = init_connection_pool(connector)
    with pool.connect() as db_conn:
        result = db_conn.execute(
            sqlalchemy.text(
                "SELECT * FROM pg_catalog.pg_roles WHERE rolname = " "'eks_users'"
            )
        ).fetchall()  # pyright: ignore [reportOptionalMemberAccess]
        result = [row for row in result]
        has_rows = len(result)
        if not has_rows:
            logger.info("No eks_users role exists. Creating...")
            db_conn.execute(sqlalchemy.text("CREATE ROLE eks_users"))
        for user in users:
            logger.info(f"Granting eks_users to '{user}'")
            db_conn.execute(sqlalchemy.text(f'GRANT eks_users to "{user}";'))

# Build query
sql_commands = ""
sql_commands += " CREATE EXTENSION IF NOT EXISTS pgaudit;"

sql_commands += " GRANT ALL ON DATABASE postgres TO eks_users;"

sql_commands += " CREATE SCHEMA IF NOT EXISTS eks AUTHORIZATION eks_users;"
sql_commands += (
    " ALTER DEFAULT PRIVILEGES IN SCHEMA eks GRANT ALL ON TABLES TO eks_users;"
)
for user in users:
    sql_commands += f' GRANT ALL ON SCHEMA eks TO "{user}";'

# initialize Connector as context manager
with Connector() as connector:
    pool = init_connection_pool(connector)
    # interact with AlloyDB database using connection pool
    with pool.connect() as db_conn:
        for cmd in sql_commands.split(";"):
            logger.info(sqlalchemy.text(cmd.strip()))
            db_conn.execute(sqlalchemy.text(cmd.strip()))
