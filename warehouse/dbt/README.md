# dbt Project

This dbt project powers the starter warehouse flow for the Omnichannel Commerce platform.

Current scope:

- raw source declarations for Olist, Retailrocket, DummyJSON, Open-Meteo, and Frankfurter
- source-aware staging models that fall back cleanly when raw tables are absent
- intermediate models for order context and clickstream sessionization
- marts for commerce orders, Retailrocket sessions, and products
- schema tests and singular tests
- CI-safe DuckDB profile plus example Postgres and BigQuery targets

Local usage:

```bash
make run-warehouse
```

That target runs the warehouse layer planner and a `dbt build` against the CI-safe DuckDB profile.

TODO:

- add incremental strategies for large raw tables
- add exposures, source freshness, and semantic documentation
- align BigQuery deployment settings with real project environments
