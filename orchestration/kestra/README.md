# Kestra Orchestration Foundations

This directory contains the local orchestration foundation for the Omnichannel Commerce platform.

Current flow:

- runs batch ingestion
- replays Retailrocket events
- plans warehouse layers
- executes `dbt build` against the CI-safe profile
- runs the Python quality runner

The flow is still shell-based. The next step is to package the project dependencies
into a dedicated image or task runner so Kestra can execute dbt and Python jobs in a
portable runtime instead of relying on the host environment.
