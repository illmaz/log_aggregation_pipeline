# Log Aggregation Pipeline

A real-time log monitoring system built with C and Python. C watches and parses log files at the system call level. Python receives, stores, detects anomalies, and visualizes the data in a live terminal dashboard.

Built as a portfolio project to demonstrate systems programming, pipeline architecture, and data engineering across two languages.

---

## Architecture

```
log file → watcher.c → Unix pipe → receiver.py → DuckDB
                                        ├── anomaly detection (threading)
                                        └── live terminal dashboard (rich)
```

- **C layer** — opens the log file, seeks to the end, polls for new bytes in a loop, parses each line into structured fields, streams JSON to stdout
- **Unix pipe** — connects C's stdout to Python's stdin — no network, no broker, no shared files
- **Python layer** — receives JSON line by line, stores in DuckDB, counts errors in time windows, alerts on spikes, renders a live dashboard

---

## Why This Stack

**C for the hot path.** Watching files, reading bytes, parsing lines — this needs to be fast with no garbage collector pausing execution. C talks directly to the OS via system calls: `open`, `lseek`, `read`, `write`. This is what Filebeat, Fluentd, and the Datadog agent do at the bottom of their abstraction stack.

**Python for the smart path.** Storage, queries, anomaly detection, dashboards — these change constantly and need flexibility. DuckDB, threading, and rich are mature tools that would take weeks to replicate in C.

**Unix pipe for transport.** The simplest possible channel between two processes. Same concept as Kafka — a producer writes, a consumer reads — without the infrastructure overhead. When this project scales, the pipe becomes a Kafka topic and nothing else changes.

---

## Requirements

- GCC
- Python 3.9+
- `pip3 install duckdb rich`

---

## How to Run

**1. Compile the watcher**

```bash
gcc watcher.c -o watcher
```

**2. Run the pipeline**

```bash
./watcher | python3 receiver.py
```

**3. Write test log lines** (second terminal)

```bash
echo "2024-01-15 03:42:11 ERROR database connection failed" >> test.log
echo "2024-01-15 03:42:12 INFO  request completed in 142ms" >> test.log
echo "2024-01-15 03:42:13 ERROR timeout after 30s" >> test.log
```

The dashboard refreshes every 10 seconds. Three or more errors in a 10-second window triggers an ALERT.

---

## Log Format

```
YYYY-MM-DD HH:MM:SS LEVEL message
```

```
2024-01-15 03:42:11 ERROR database connection failed
2024-01-15 03:42:12 INFO  request completed in 142ms
2024-01-15 03:42:13 WARN  memory usage above 80%
```

---

## Project Phases

| Phase | Layer | What was built |
|-------|-------|----------------|
| 1 | C | Tail a log file in real time using `open`, `lseek`, `read` |
| 2 | C | Parse log lines into timestamp, level, message using structs |
| 3 | C → Python | Stream parsed data as JSON over a Unix pipe |
| 4 | Python | Receive JSON and store in DuckDB |
| 5 | Python | Detect error spikes using time windows and threading |
| 6 | Python | Live terminal dashboard with rich |

---

## Real-World Connections

| This project | Production equivalent |
|---|---|
| `watcher.c` | Filebeat, Fluentd, Datadog agent |
| Unix pipe | Kafka topic |
| DuckDB | Elasticsearch, ClickHouse |
| Anomaly detection | Datadog monitors, Grafana alerts |
| Terminal dashboard | Grafana, Datadog dashboards |
