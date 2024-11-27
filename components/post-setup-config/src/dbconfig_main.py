import os

import sqlalchemy
from google.cloud.alloydb.connector import Connector, IPTypes


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


# Create role if not exists
with Connector() as connector:
    pool = init_connection_pool(connector)
    with pool.connect() as db_conn:
        result = db_conn.execute(
            sqlalchemy.text(
                "SELECT * FROM pg_catalog.pg_roles WHERE rolname = ""'eks_users'")
        ).fetchall()  # pyright: ignore [reportOptionalMemberAccess]
        result = [row for row in result]
        print(result)
        has_rows = len(result)
        if not has_rows:
            db_conn.execute(sqlalchemy.text('CREATE ROLE eks_users'))

# Build query
sql_commands = ""
sql_commands += " CREATE EXTENSION IF NOT EXISTS pgaudit;"
users = [os.environ["ALLOYDB_USER_CONFIG"], os.environ["ALLOYDB_USER_SPECIALIZED_PARSER"], "postgres"]

sql_commands += " GRANT ALL ON DATABASE postgres TO eks_users;"
sql_commands += " SET ROLE eks_users;"

sql_commands += " CREATE SCHEMA IF NOT EXISTS eks AUTHORIZATION eks_users;"
sql_commands += " ALTER DEFAULT PRIVILEGES IN SCHEMA eks GRANT ALL ON TABLES TO eks_users;"
for user in users:
    sql_commands += f' GRANT eks_users to "{user}";'
    sql_commands += f' GRANT ALL ON SCHEMA eks TO "{user}";'

# initialize Connector as context manager
with Connector() as connector:
    pool = init_connection_pool(connector)
    # interact with AlloyDB database using connection pool
    with pool.connect() as db_conn:
        db_conn.execute(sqlalchemy.text(sql_commands))
