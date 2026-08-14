# scripts/

## `KARDS_LOAD_DATA.py`

Local ingestion script — the first stage of the pipeline. Runs on a machine with
direct access to the source SQL Server database (Fabric's cloud compute cannot
reach a local, on-premises server without a gateway).

**What it does, in order:**

1. Connects to the local SQL Server (`KardsWarehouse` database) via SQLAlchemy/pyodbc.
2. Exports `kards.KARDS`, `kards.SPAWNABLES`, and `kards.FORECAST` to local Parquet
   files, each with independent retry logic (up to 5 attempts). Login failures
   (`InterfaceError`) stop immediately since retrying won't fix a wrong password;
   connection/network failures (`OperationalError`) retry.
3. Only proceeds to upload if all three exports succeeded.
4. Authenticates to Azure using `InteractiveBrowserCredential`, with a cached
   `AuthenticationRecord` (`auth_record.json`, git-ignored) so repeat runs don't
   require a fresh browser login every time.
5. Uploads each Parquet file directly into the Fabric Lakehouse's `Files` section
   via the OneLake/ADLS Gen2 API (`azure-storage-file-datalake`).

**Credentials:** read from environment variables (`KARDS_DB_USER`,
`KARDS_DB_PASSWORD`), never hardcoded. See the repo root `README.md` for how to set
these.

**Scheduling:** run via Windows Task Scheduler on a daily trigger. Must run in a
session where the user is logged in, since the interactive Azure auth flow needs an
active desktop session (unless/until migrated to a non-interactive credential such
as a Service Principal).

## `requirements.txt`

Python dependencies for this script. Install with:

```bash
pip install -r requirements.txt
```
