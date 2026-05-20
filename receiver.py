import sys
import json
import duckdb
import threading
import time

con = duckdb.connect("logs.db")

con.execute("""
            CREATE TABLE IF NOT EXISTS logs (
            timestamp TEXT,
            log_level TEXT,
            message TEXT
            )
        """)

error_count = 0
lock = threading.Lock()
THRESHOLD = 3
WINDOW_SECONDS = 10

def check_errors():
    global error_count
    while True:
        time.sleep(WINDOW_SECONDS)
        with lock:
            count = error_count
            error_count = 0
        if count >= THRESHOLD:
            print(f"ALERT: {count} errors in the last {WINDOW_SECONDS} seconds")
        else:
            print(f"OK: {count} errors in the last {WINDOW_SECONDS} seconds")

checker = threading.Thread(target=check_errors, daemon=True)
checker.start()



for line in sys.stdin:
    line = line.strip()
    if not line:
        continue

    entry = json.loads(line)
    con.execute("INSERT INTO logs VALUES (?, ?, ?)",
                [entry['timestamp'], entry['level'], entry['message']])
    print(f"Stored: {entry['timestamp']} | {entry['level']} | {entry['message']}")

    if entry['level'] == 'ERROR':
        with lock:
            error_count += 1