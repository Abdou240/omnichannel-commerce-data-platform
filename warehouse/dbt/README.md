# dbt Project

This dbt project powers the starter warehouse flow for the Omnichannel Commerce platform.

Current scope:

- raw source declarations for Olist, Retailrocket, Open Food Facts, Open-Meteo, and Frankfurter
- source-aware staging models that fall back cleanly when raw tables are absent
- intermediate models for order context and clickstream sessionization
- marts for commerce orders, Retailrocket sessions, and products
- schema tests and singular tests
- CI-safe DuckDB profile plus example Postgres and BigQuery targets
- public BigQuery reference metadata for GA4 sample ecommerce and the Look eCommerce

Local usage:

```bash
make run-warehouse
```

That target runs the warehouse layer planner and a `dbt build` against the CI-safe DuckDB profile.

TODO:

- add incremental strategies for large raw tables
- add exposures, source freshness, and semantic documentation
- align BigQuery deployment settings with real project environments
- add BigQuery-targeted starter models that query the public GA4 and the Look datasets directly
