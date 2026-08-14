# notebooks/

## Bronze → Silver → Gold notebook

Exported from the Fabric workspace notebook. Contains the PySpark logic for the
Lakehouse side of the medallion pipeline. Requires a Fabric environment (or a Spark
session with Delta Lake support) to run — the `spark` object used throughout is
Fabric's pre-provisioned `SparkSession`, not something created in the notebook
itself.

**What it does, in order:**

1. **Bronze** — reads the three Parquet files landed in the Lakehouse's `Files`
   section (via the ingestion script in `scripts/`) and writes them unchanged as
   Delta tables: `bronze.kards`, `bronze.spawnables`, `bronze.forecast`.

2. **Silver** — reads from Bronze and writes cleaned versions to `silver.*`:
   - `kards`: explicit column selection, dropping image paths and audit timestamps
     not needed for analysis.
   - `spawnables`, `forecast`: only image-path columns dropped, since both are
     treated as reference/master data with otherwise-complete columns.
   - Includes a null-count diagnostic pattern
     (`sum(when(col(c).isNull(), 1).otherwise(0))` per column) used to confirm most
     nulls in `KARDS` are structurally expected (e.g. veteran-only stat columns are
     null for non-veteran cards), not data quality issues.

3. **Gold (Lakehouse)** — reads from Silver and writes:
   - `kards`, `spawnables`, `forecast` — full conformed copies, kept as
     general-purpose base tables.
   - `spawn_chain` — KARDS (`IsSpawnable = True`) joined to SPAWNABLES on `CardId`,
     duplicate join key dropped.
   - `eligible_for_forecast`, `veteran_cards`, `permanent_pool_cards` — single-table
     filters on `IsForecastable`, `IsVeteran`, `IsPermanentPool` respectively.

Bronze is read-only throughout this notebook — every write targets Silver or Gold,
never Bronze itself, so the raw source snapshot is always recoverable.
