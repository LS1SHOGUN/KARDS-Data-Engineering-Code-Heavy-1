import pandas as pd
import logging
import sqlalchemy as sa
import sqlalchemy.exc
import os
from azure.identity import InteractiveBrowserCredential, TokenCachePersistenceOptions, AuthenticationRecord
from azure.storage.filedatalake import DataLakeServiceClient

logging.basicConfig(
    filename="KARDSLOG.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.getLogger("azure").setLevel(logging.WARNING)

# ---------- PART 1: EXPORT FROM SQL SERVER ----------

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

record_path = "auth_record.json"
if os.path.exists(record_path):
    with open(record_path, "r") as f:
        record = AuthenticationRecord.deserialize(f.read())
    credential = InteractiveBrowserCredential(
        cache_persistence_options=TokenCachePersistenceOptions(),
        authentication_record=record
    )
else:
    credential = InteractiveBrowserCredential(
        cache_persistence_options=TokenCachePersistenceOptions()
    )
    record = credential.authenticate()
    with open(record_path, "w") as f:
        f.write(record.serialize())

service_client = DataLakeServiceClient(
    account_url="https://onelake.dfs.fabric.microsoft.com",
    credential=credential
)

def do_something(query, engine):
    logging.info("Connected to database")
    df = pd.read_sql_query(query, engine)
    logging.info(f"Loaded {len(df)} rows successfully")
    return df

def load_table(query, filename, engine, max_attempts=5):
    attempt = 1
    success = False
    while attempt <= max_attempts and not success:
        try:
            df = do_something(query, engine)
            df.to_parquet(filename)
            success = True
        except sqlalchemy.exc.InterfaceError as e:
            logging.error(f"Login failed, not retrying: {e}")
            break
        except sqlalchemy.exc.OperationalError as e:
            logging.error(f"Attempt {attempt} failed: {e}")
            attempt += 1
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            break
    if not success:
        logging.error(f"Failed to load {filename} after all attempts")
    return success

def load_data(file_name):
    try:
        logging.info(f"Uploading {file_name} to Lakehouse")
        file_system_client = service_client.get_file_system_client(file_system="KARDS Data Engineering")
        directory_client = file_system_client.get_directory_client("KardsLakeHouse.Lakehouse/Files")
        file_client = directory_client.get_file_client(file_name)
        with open(file_name, "rb") as f:
            file_client.upload_data(f, overwrite=True)
        logging.info(f"Uploaded {file_name} successfully")
        return True
    except Exception as e:
        logging.error(f"Failed to upload {file_name}: {e}")
        return False

logging.info("Export pipeline started")

tables = ["KARDS", "SPAWNABLES", "FORECAST", "EXILE", "SYNERGY_TAG_RULES", "SYNERGY_COMBO_RULES"]

for table in tables:
    query = f"select * from kards.{table}"
    file_name = f"{table}.parquet"
    if load_table(query, file_name, engine):
        logging.info(f"Loaded {file_name} successfully")
        logging.info("Upload to Lakehouse started")
        upload_results = load_data(file_name)
        if upload_results:
            logging.info("Upload to Lakehouse completed successfully")
        else:
            logging.error("Upload failed")
