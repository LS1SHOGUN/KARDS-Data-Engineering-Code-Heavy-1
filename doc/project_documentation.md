# Kards Data Engineering Project — Version 1 (Code-First)

## Overview

An end-to-end medallion architecture data pipeline built on Microsoft Fabric, using
real data from a personal ASP.NET MVC web application ("Kards" — a trading-card-game
collection manager backed by SQL Server via Entity Framework). The pipeline moves data
from a local SQL Server database through Bronze, Silver, and Gold layers, and surfaces
it in Power BI.

Version 1 is the **code-first** implementation: Python/pandas for ingestion, PySpark
for the Lakehouse transformation layer, and T-SQL for a parallel Warehouse
implementation of Gold. A second, low-code version (Dataflow Gen2 / template-driven)
is planned separately.

**Source system:** SQL Server (`KardsWarehouse` database), three tables:
- `kards.KARDS` — the card catalog (28 columns: stats, nation, rarity, cost, veteran
  variants, spawnable/forecastable flags, expansion/rotation info)
- `kards.SPAWNABLES` — child "spawn" cards linked to a parent card via `CardId`
- `kards.FORECAST` — a static master table of weather-mechanic cards (Blue Sky/Mist/Gale)

---

## Architecture

```
Local SQL Server (SWETHA)
        │
        ▼  pandas export (retry-safe, logged)
   Parquet files (local disk)
        │
        ▼  OneLake API upload (cached Azure auth)
   Lakehouse Files
        │
        ▼  PySpark (spark.read.parquet → saveAsTable)
   ┌─────────────┐
   │   BRONZE    │  raw, untouched, one-to-one with source
   └─────────────┘
        │
        ▼  PySpark (select/drop columns, no row-level changes)
   ┌─────────────┐
   │   SILVER    │  cleaned column set, correct types
   └─────────────┘
        │
        ├──────────────────────────────┐
        ▼ PySpark (Lakehouse)          ▼ T-SQL (Warehouse, via cross-item query)
   ┌─────────────┐                ┌─────────────────┐
   │    GOLD     │                │   GOLD (T-SQL)   │
   │  (Lakehouse)│                │   (Warehouse)    │
   └─────────────┘                └─────────────────┘
        │                                  │
        └──────────────┬───────────────────┘
                        ▼
                  Power BI reports
             (two semantic models:
              Lakehouse Gold, Warehouse Gold)
```

Medallion principle followed throughout: **Bronze is never written to after initial
load** — every transformation reads from Bronze/Silver and writes only to the next
layer down, so raw source data is always recoverable without re-querying the source
system.

---

## Layer-by-layer detail

### Bronze
- Populated by reading the three uploaded Parquet files from the Lakehouse's `Files`
  section and writing them as Delta tables: `bronze.kards`, `bronze.spawnables`,
  `bronze.forecast`.
- No transformation logic — exact copy of source data.

### Silver
- Built from Bronze via `.select()` (KARDS — explicit column keep-list, dropping
  image paths and audit timestamps) and `.drop()` (SPAWNABLES, FORECAST — only image
  path columns removed, everything else retained since both are treated as
  reference/master data).
- Null-quality check performed using a PySpark null-count pattern
  (`sum(when(col(c).isNull(), 1).otherwise(0))` per column) — confirmed most nulls in
  KARDS are structurally legitimate (e.g. veteran stat columns are null for the ~97%
  of cards that aren't veteran variants), not data quality defects requiring cleanup.

### Gold — built twice, deliberately

**Lakehouse Gold (PySpark):**
- `gold.kards`, `gold.spawnables`, `gold.forecast` — full conformed copies of Silver,
  kept as general-purpose base tables for flexible BI access without repeated joins.
- `gold.spawn_chain` — KARDS (`IsSpawnable = True`) inner-joined to SPAWNABLES on
  `CardId`, duplicate join key dropped post-join.
- `gold.eligible_for_forecast` — KARDS filtered on `IsForecastable = True`.
- `gold.veteran_cards` — KARDS filtered on `IsVeteran = True`.
- `gold.permanent_pool_cards` — KARDS filtered on `IsPermanentPool = True`.

**Warehouse Gold (T-SQL):**
- Same six tables, rebuilt independently using `CREATE TABLE ... AS SELECT` against
  the Lakehouse's Silver tables via Fabric's cross-item querying
  (`KardsLakehouse.silver.kards`).
- Refresh pattern implemented as `TRUNCATE TABLE` + `INSERT INTO ... SELECT`, since
  CTAS only runs once against a non-existent table — this is the pattern used for
  repeatable, scheduled refreshes.
- `spawn_chain` stamped with its own build date (`CAST(GETDATE() AS DATE)`) rather
  than inheriting source-row audit timestamps, since the date describes when the Gold
  table itself was materialized.

Building Gold twice — once in Spark, once in T-SQL — was a deliberate choice to
demonstrate both engines rather than picking one, directly relevant to DP-700 exam
prep and to showing SQL-transferable skills.

---

## Ingestion pipeline (automation)

**Local export + upload script** (Python, run via Task Scheduler):
1. Connects to SQL Server via SQLAlchemy/pyodbc.
2. Exports each of the three tables to Parquet with independent retry logic per
   table — up to 5 attempts, distinguishing `InterfaceError` (login failure — stop
   immediately, retrying won't help) from `OperationalError` (connection/network —
   worth retrying).
3. Only proceeds to upload if **all three** exports succeeded.
4. Authenticates to Azure via `InteractiveBrowserCredential` with
   `TokenCachePersistenceOptions` and a saved `AuthenticationRecord`, so subsequent
   runs reuse the cached token instead of prompting a login every time.
5. Uploads each Parquet file directly to the Lakehouse's `Files` section via the
   OneLake / ADLS Gen2-compatible SDK (`azure-storage-file-datalake`), with per-file
   try/except and logging.
6. Full run logged to `KARDSLOG.txt`; Azure SDK's own verbose request/response
   logging suppressed (`logging.getLogger("azure").setLevel(logging.WARNING)`) to
   keep the log readable.
7. Scheduled via Windows Task Scheduler (daily trigger), running only when the user
   is logged in (required for the interactive-auth flow to have a desktop session).

**On-premises Data Gateway:**
- Installed and registered to enable direct Fabric-to-local-SQL-Server connectivity,
  removing the earlier limitation where the Fabric-hosted notebook's Linux-based
  Spark environment couldn't reach a Windows ODBC driver or the local network.
- A registered connection (`KARDS_server`, via gateway `local_gateway`) enables a
  proper Data Factory Copy Data pipeline as an alternative ingestion path.

**Warehouse Gold refresh pipeline:**
- A Fabric Data Pipeline with a Script activity runs the TRUNCATE + INSERT batch
  against the Warehouse on a schedule, automating the Gold refresh without manual
  SQL editor execution.

---

## Reporting

Two semantic models built from the two Gold implementations (`Warehouse Gold`,
`Lakehouse Gold`), with relationships explicitly defined between related tables
(`kards` ↔ `spawnables` on `CardId`). Derived filter-only tables
(`veteran_cards`, `eligible_for_forecast`, `permanent_pool_cards`) were evaluated as
candidates for report-level filters rather than separate model tables, to avoid
disconnected/duplicated data in the model.

**Power BI report** (`KARDS-REPORT-WAREHOUSE`), three visuals:
1. **Bar chart** — count of cards by `CardNation`, color-coded by nation via Legend.
   Confirms Japan as the dominant nation by card count.
2. **Table** — `spawn_chain`, browsable parent-card-to-spawn-card relationships with
   stats (`CardName`, `CardNation`, `SpawnCardName`, `SpawnCardType`,
   `SpawnAttack`, `SpawnHitPoint`).
3. **Pie chart** — veteran card count by nation. Surfaced a genuine, non-obvious
   insight: despite Japan having by far the most total cards, veteran variants are
   concentrated 80% in ANZAC and only 20% in Japan — veteran status does not scale
   with overall card count.

---

## Problems solved along the way

- **`localhost\SWETHA` named-instance connection formatting** — resolved by testing
  both bare hostname and `localhost\instance` forms.
- **Notebook item confusion** — Fabric trial capacity initially only exposed
  "Spark query" (SQL-only) rather than a general-purpose Notebook item; resolved by
  creating the notebook from the workspace level and attaching the Lakehouse
  explicitly.
- **Local-to-cloud connectivity gap** — Fabric's cloud compute (Linux-based) cannot
  reach a local Windows SQL Server without either an On-premises Gateway or a
  manual export/upload step. Solved short-term via the pandas export + OneLake API
  upload script, and longer-term via the gateway.
- **Repeated interactive login** — solved with `TokenCachePersistenceOptions` plus
  an explicitly saved/reloaded `AuthenticationRecord` (automatic cache alone was
  insufficient; the credential needs to be told which account to silently resume).
- **PySpark case sensitivity** — `.isnull()` (lowercase) silently resolved to
  PySpark's struct-field-access syntax instead of throwing a clear error, producing
  a confusing `'Column' object is not callable` error; the fix was the correctly
  cased `.isNull()`.
- **Logging noise** — Azure SDK's own HTTP-level logging was flooding the log file
  once it shared the root logger with the application's own `logging.info()` calls;
  resolved by raising the `"azure"` logger's level independently.
- **Duplicate join columns** — both `.join()` (PySpark) and the T-SQL equivalent
  needed explicit handling to avoid two `CardId` columns in `spawn_chain`.

---

## Skills demonstrated

Python (functions, control flow, retry/backoff patterns), pandas (transformation
logic paralleling SQL joins/aggregates), SQLAlchemy/pyodbc connectivity, structured
exception handling and logging, Azure identity and OneLake/ADLS Gen2 API usage,
PySpark (DataFrame operations, lazy evaluation awareness, Delta table writes), T-SQL
(CTAS, TRUNCATE/INSERT refresh patterns, cross-item Warehouse-to-Lakehouse queries),
Fabric platform navigation (Lakehouse, Warehouse, Data Pipelines, On-premises
Gateway), Windows Task Scheduler automation, and Power BI semantic modeling and
report building.
