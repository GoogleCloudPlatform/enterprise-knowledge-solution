from google.cloud.alloydb.connector import Connector, IPTypes
import os
import sqlalchemy

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

# initialize Connector as context manager
with Connector() as connector:
    sql_commands = f'CREATE SCHEMA IF NOT EXISTS eks;'
    sql_commands += f' CREATE EXTENSION IF NOT EXISTS pgaudit;'
    users = [os.environ["ALLOYDB_USER_SPECIALIZED_PARSER"], "postgres"]
    for user in users:
        sql_commands += f' GRANT ALL ON SCHEMA eks TO "{user}";'
        sql_commands += f' GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA eks TO "{user}";'
        sql_commands += f' GRANT USAGE ON SCHEMA eks TO "{user}";'
    print(sql_commands)

    pool = init_connection_pool(connector)
    # interact with AlloyDB database using connection pool
    with pool.connect() as db_conn:
        db_conn.execute(sqlalchemy.text(sql_commands))
