# sql/

T-SQL for the Warehouse implementation of the Gold layer — built as a parallel,
independent version of the same Gold tables produced by the PySpark notebook, using
Fabric's Warehouse item and cross-item queries against the Lakehouse's Silver
tables.

## `gold_warehouse_build.sql`

Initial build script. Creates the `GOLD` schema and all six Gold tables using
`CREATE TABLE ... AS SELECT` (CTAS), reading directly from
`KardsLakehouse.silver.*` via Fabric's cross-item querying — no data is copied out
of the Lakehouse manually.

Tables created: `spawn_chain`, `eligible_for_forecast`, `veteran_cards`,
`permanent_pool_cards`, plus full conformed copies of `kards`, `spawnables`, and
`forecast`.

Run this once, against an empty Warehouse. Running it a second time will fail
(CTAS requires the target table not already exist) — use the refresh script instead
for subsequent runs.

## `gold_warehouse_refresh.sql`

Repeatable refresh script, for tables that already exist. Uses
`TRUNCATE TABLE` + `INSERT INTO ... SELECT` per table, which clears existing rows
while keeping the table structure intact, then repopulates from the current state
of Silver.

This is the script wired into the scheduled Data Pipeline Script activity that
automates the Gold refresh.

**Note:** `spawn_chain` is stamped with `CAST(GETDATE() AS DATE)` as its build date,
rather than inheriting a source row's own audit timestamp — this reflects when the
Gold table itself was last materialized, not when a source record was created.
