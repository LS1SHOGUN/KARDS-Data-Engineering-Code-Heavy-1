# docs/

## `project_documentation.md`

Full architecture write-up for the project — overview, layer-by-layer detail for
Bronze/Silver/Gold (both the PySpark/Lakehouse and T-SQL/Warehouse
implementations), the ingestion automation design, the reporting layer, problems
solved during the build, and a summary of skills demonstrated.

## Pipeline definition (JSON)

Exported definition of the Fabric Data Pipeline used to automate the Gold Warehouse
refresh (a Script activity running `sql/gold_warehouse_refresh.sql` on a schedule).
Included for reference/portability — re-importing this JSON into a Fabric workspace
recreates the pipeline's activities and configuration without rebuilding it by
hand.
