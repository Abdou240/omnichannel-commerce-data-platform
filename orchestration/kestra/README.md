# Kestra Orchestration Foundations

This directory contains the local orchestration foundation for the Omnichannel Commerce platform.

Current flow:

- runs batch ingestion
- replays Retailrocket events
- logs warehouse layer planning
- runs the Python quality runner

The flow is intentionally still shell-based. The next step is to package the project dependencies
into a dedicated image or task runner so Kestra can execute dbt and Python jobs without relying on
the host environment.
