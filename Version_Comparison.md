# Kards Data Engineering Pipeline — Version Comparison

Two independent implementations of the same medallion architecture (Bronze → Silver →
Gold → Power BI), built on the same source data, using deliberately different
approaches — one code-first, one low-code. Built to compare the two paradigms
directly rather than picking one.

## At a glance

| | Version 1 (Code-Heavy) | Version 2 (Low-Code) |
|---|---|---|
| **Lakehouse** | `KardsLakehouse` | `KardsLakehouseV2` (fully separate) |
| **Ingestion (Bronze)** | Python/pandas script → OneLake API upload, scheduled via Windows Task Scheduler | Data Factory Copy Data pipeline via On-premises Data Gateway |
| **Silver transformation** | PySpark notebook (`.select()`/`.drop()`) | Dataflow Gen2 (Power Query, visual column removal) |
| **Gold transformation** | PySpark notebook + a parallel T-SQL Warehouse build | Dataflow Gen2 (Power Query, Merge Queries + Filter Rows) |
| **Reporting** | Power BI, two semantic models (Lakehouse Gold, Warehouse Gold) | Power BI, semantic model on `KardsLakehouseV2` Gold |
| **Automation** | Local script scheduling + a separate Data Pipeline Script activity for the Warehouse refresh | Native Fabric scheduling on the Dataflows/pipeline — no local machine dependency |

---

## Version 1: Code-Heavy

### Advantages
- **Full control over transformation logic.** Every null-handling decision, every
  column cast, every join condition is explicit code — nothing hidden behind a UI.
- **Version-controllable.** The notebook and T-SQL scripts are plain text, so they
  live cleanly in Git with real history, diffs, and code review potential.
- **Reusable, parametrized patterns.** The `load_table()` retry function and the
  dynamic `add_null_flags()` pattern generalize to any table or column list —
  something a visual tool can't express as cleanly.
- **Demonstrates two engines side by side.** Building Gold in both PySpark and
  T-SQL against the same Silver data is a genuine, deliberate skill demonstration
  that a single low-code tool can't replicate.
- **Transferable skills.** Python, pandas, and PySpark syntax carry directly into
  any other data platform (Databricks, plain Spark, other clouds) — none of it is
  Fabric-specific.

### Disadvantages
- **Higher setup cost.** Getting from zero to a working pipeline required solving
  real infrastructure problems — local-to-cloud connectivity, Azure authentication
  and token caching, retry logic — before any actual data work could begin.
- **More moving parts to maintain.** A local Python script, a scheduled Windows
  task, notebook cells, and separate T-SQL scripts all need to stay in sync
  independently.
- **Depends on local infrastructure.** The original ingestion script only runs
  if the local machine is on, logged in, and the environment variables are set —
  a real operational fragility that a cloud-native pipeline doesn't have.
- **Steeper learning curve.** Every step required understanding a new concept
  (lazy evaluation, `col()` vs. attribute access, window functions, Delta's
  transaction log) before it could be used correctly.

---

## Version 2: Low-Code

### Advantages
- **Faster to build, once the gateway works.** With the On-premises Data Gateway
  in place, connecting a new source or building a transformation is largely
  drag-and-drop — no code to write or debug for the transformation logic itself.
- **Runs entirely in the cloud.** The Data Factory pipeline and both Dataflows
  execute on Fabric's own compute, with no dependency on a local machine being on
  — a genuine reliability advantage over Version 1's local script.
- **Lower barrier for non-coders.** Business users or analysts without Python/SQL
  background could maintain or extend this pipeline directly through the visual
  interface.
- **Fabric-native scheduling.** No Windows Task Scheduler, no environment
  variables, no local credential management — scheduling and auth are handled
  entirely inside Fabric.
- **Faster iteration on simple changes.** Removing a column or adding a filter
  condition is a few clicks, versus editing and re-running code.

### Disadvantages
- **Less precise control over edge cases.** Complex conditional logic (like the
  dynamic, parametrized null-flagging function built in Version 1) is awkward or
  impossible to express cleanly in Power Query's visual interface.
- **Harder to version-control meaningfully.** Dataflow Gen2's underlying
  definition can be exported, but reviewing a diff of visual transformation steps
  is far less readable than a code diff.
- **The gateway setup itself was the hardest part of this whole version.**
  Ironically, the "low-code" version required the most infrastructure
  troubleshooting of the entire project — a transient cloud relay error, a
  service-account permissions issue, and an encrypted-connection mismatch between
  the gateway and the local SQL Server, none of which had anything to do with the
  actual transformation logic.
- **Skills are more platform-specific.** Power Query/Dataflow Gen2 expertise
  transfers to Power BI and Excel, but far less directly to other data engineering
  platforms than Python/SQL do.

---

## What building both actually demonstrated

Building the same outcome twice — once explicit and code-driven, once visual and
declarative — surfaced a genuine, defensible answer to "when would you choose
one over the other," rather than a preference stated in the abstract:

- **Choose code-first** when the transformation logic is complex, needs to be
  reused across many similar cases, needs rigorous version control and code
  review, or when the team already has strong SQL/Python skills (as in this
  case, coming from a T-SQL/SSIS background).
- **Choose low-code** when the logic is genuinely simple (filters, straightforward
  joins, column selection), the team includes non-coders, or fast iteration on
  business-facing changes matters more than precise control.
- **In practice, many real teams use both** — exactly the pattern built here:
  code for the parts that need precision and reuse, low-code for straightforward
  movement and shaping, both feeding the same reporting layer.

The infrastructure lesson that applied equally to both versions: the hardest,
most time-consuming problems in this entire project were never the transformation
logic itself — they were connectivity, authentication, and credential management.
That held true whether the transformation was written in PySpark or built with a
mouse.
