# Kards Fabric Data Pipeline

An end-to-end medallion architecture (Bronze → Silver → Gold) data pipeline built on
Microsoft Fabric, using real data from a personal trading-card-game collection app
([KARDS-WEB-PROJECT](https://github.com/LS1SHOGUN/KARDS-WEB-PROJECT)) backed by SQL
Server.

## What this project does

Pulls card and card-relationship data from a local SQL Server database, lands it raw
in a Fabric Lakehouse (Bronze), cleans and shapes it (Silver), then builds
analysis-ready Gold tables two ways — once in PySpark (Lakehouse) and once in T-SQL
(Warehouse) — before surfacing everything in Power BI.

Full write-up: [`doc/project_documentation.md`](docs/project_documentation.md)

## Architecture

```
Local SQL Server → pandas export (retry-safe) → OneLake upload (cached auth)
   → Bronze (PySpark) → Silver (PySpark) → Gold (PySpark + T-SQL, in parallel)
   → Power BI (two semantic models)
```

## Repository structure

```
├── scripts/    Python ingestion script + dependency list
├── notebooks/  Fabric notebook (Bronze → Silver → Gold, PySpark)
├── sql/        Warehouse Gold build + refresh T-SQL
└── docs/       Full project write-up + exported pipeline definition
```

Each subfolder has its own `README.md` with more detail.

## Setup

1. `pip install -r scripts/requirements.txt`
2. Set the following environment variables before running the export script:
   - `KARDS_DB_USER`, `KARDS_DB_PASSWORD` (SQL Server credentials)
   - `KARDS_DB_SERVER`, `KARDS_DB_NAME` (optional — have sensible defaults)
3. Run `scripts/KARDS_LOAD_DATA.py` to export from SQL Server and upload to OneLake.
4. Run the notebook cells in `notebooks/` inside Fabric to build Bronze → Silver → Gold.
5. Run `sql/gold_warehouse_build.sql` once in the Fabric Warehouse's SQL editor to
   create the parallel T-SQL Gold layer; use `sql/gold_warehouse_refresh.sql` for
   subsequent refreshes.

## Notes

- Credentials are never hardcoded — the export script reads them from environment
  variables.
- `auth_record.json` (a local Azure auth token cache) and log files are intentionally
  excluded via `.gitignore` and are not present in this repo.
- Gold is built twice on purpose — once in PySpark against the Lakehouse, once in
  T-SQL against the Warehouse — to demonstrate both engines rather than picking one.
