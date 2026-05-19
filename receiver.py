import sys
import json
import duckdb

con = duckdb.connect("logs.db")

con.execute("""
            CREATE TABLE IF NOT EXISTS logs (
            timestamp TEXT,
            log_level TEXT,
            message TEXT
            )
        """)


for line in sys.stdin:
    line = line.strip()
    if not line:
        continue

    entry = json.loads(line)
    con.execute("INSERT INTO logs VALUES (?, ?, ?)",
                [entry['timestamp'], entry['level'], entry['message']])
    print(f"Stored: {entry['timestamp']} | {entry['level']} | {entry['message']}")
