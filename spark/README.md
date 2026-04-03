# Spark Starter Assets

This directory contains the starter Spark path for distributed clickstream processing.

Current scope:

- local Spark defaults example
- Retailrocket sessionization job at `spark/jobs/clickstream_sessionization.py`

Local usage:

```bash
make spark-sessionize
```

The current job reads the sample Retailrocket replay file, applies a 30-minute session gap, and
writes parquet session summaries under `storage/gold/retailrocket_sessions`.

TODO:

- package jobs for cluster or serverless execution
- write results to object storage or a warehouse table
- add checkpointing for long-running streaming workloads
