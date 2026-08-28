import time
import pandas as pd
import logging
import sqlalchemy as sa
import os
from azure.storage.filedatalake import DataLakeServiceClient

def create_log():
    logging.basicConfig(
        filename="KARDS_PIPELINE_LOG.txt",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    logging.getLogger("azure").setLevel(logging.WARNING)

def connect_to_db():
    username = os.environ.get("KARDS_DB_USER")
    password = os.environ.get("KARDS_DB_PASSWORD")
    server = os.environ.get("KARDS_DB_SERVER", "SWETHA")
    database = os.environ.get("KARDS_DB_NAME", "KardsWarehouse")

    if not username or not password:
        raise ValueError("KARDS_DB_USER and KARDS_DB_PASSWORD environment variables must be set")

    connection_string = (
        f"mssql+pyodbc://{username}:{password}@{server}/{database}"
        "?driver=ODBC+Driver+17+for+SQL+Server"
    )

    engine = sa.create_engine(connection_string)
    return engine

from azure.identity import ClientSecretCredential

def connect_to_cloud():
    credential = ClientSecretCredential(
        tenant_id=os.environ["AZURE_TENANT_ID"],
        client_id=os.environ["AZURE_CLIENT_ID"],
        client_secret=os.environ["AZURE_CLIENT_SECRET"]
    )
    service_client = DataLakeServiceClient(
        account_url="https://onelake.dfs.fabric.microsoft.com",
        credential=credential
    )
    return service_client

def fetch_source_data(query,engine,full_path):
    df = pd.read_sql_query(query,engine)
    df.to_parquet(full_path)


def load_bronze_file(file_path,file_name,service_client):
    file_system_client = service_client.get_file_system_client(file_system="KARDS Data Engineering")
    directory_client = file_system_client.get_directory_client("KardsLakeHouse.Lakehouse/Files")
    file_client = directory_client.get_file_client(file_name)
    with open(file_path, "rb") as f:
        file_client.upload_data(f, overwrite=True)

def main():
    engine = connect_to_db()
    table_query = "select a.name TableName from sys.tables a join sys.schemas b on a.schema_id = b.schema_id where b.name = 'kards'"
    tdf = pd.read_sql_query(table_query, engine)
    tables = tdf["TableName"].tolist()
    engine = connect_to_db()
    service_client = connect_to_cloud()
    create_log()
    logging.info("Pipeline started")
    for table in tables:
        query = f"select * from kards.{table}"
        #file_path = "C:\\Users\\swethakarunamoorthy\\PycharmProjects\\KARDS-Data-Engineering-Code-Heavy-1\\data"
        file_path = os.environ.get("KARDS_DATA_DIR", "/opt/airflow/kards_data")#changed windows path to docker ath
        file_name = f"{table}.parquet"
        full_path = os.path.join(file_path, file_name)
        logging.info(f"Fetching data from {table}")
        fetch_source_data(query,engine,full_path)
        logging.info(f"Fetching data from {table} complete as file {file_name}")
        logging.info(f"Loading into Lakehouse for file {file_name} is started")
        load_bronze_file(full_path,file_name,service_client)
        logging.info(f"Loading into Lakehouse for file {file_name} is completed")
        time.sleep(5)
    logging.info("Pipeline completed")

if __name__ == "__main__":
    main()