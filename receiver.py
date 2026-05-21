import sys
import json
import duckdb
import threading
import time
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich import box

con = duckdb.connect("logs.db")

con.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        timestamp TEXT,
        log_level TEXT,
        message TEXT
    )
""")

error_count = 0
total_logs = 0
lock = threading.Lock()
THRESHOLD = 3
WINDOW_SECONDS = 10
console = Console()

def check_errors(live):
    con_checker = duckdb.connect("logs.db")
    global error_count
    while True:
        try:
            time.sleep(WINDOW_SECONDS)
            with lock:
                count = error_count
                error_count = 0
                current_total = total_logs

            status = "ALERT" if count >= THRESHOLD else "OK"
            recent_logs = con_checker.execute("""
                SELECT timestamp, log_level, message
                FROM logs
                ORDER BY rowid DESC
                LIMIT 5
            """).fetchall()

            table = Table(box=box.SIMPLE, title=f"STATUS: {status} | ERRORS: {count} in last {WINDOW_SECONDS}s | TOTAL: {current_total}")
            table.add_column("Timestamp", style="cyan")
            table.add_column("Level", style="white")
            table.add_column("Message", style="white")

            for log in recent_logs:
                level_style = "red" if log[1] == "ERROR" else "green"
                table.add_row(log[0], f"[{level_style}]{log[1]}[/{level_style}]", log[2])

            live.update(table)
        except Exception as e:
            console.print(f"[red]checker error: {e}[/]")

with Live(Table(), refresh_per_second=1) as live:
    checker = threading.Thread(target=check_errors, args=(live,), daemon=True)
    checker.start()
    time.sleep(0.5)

    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue

            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            timestamp = entry.get('timestamp', 'unknown')
            level = entry.get('level', 'unknown')
            message = entry.get('message', 'unknown')

            con.execute("INSERT INTO logs VALUES (?, ?, ?)",
                        [timestamp, level, message])

            with lock:
                total_logs += 1
                if level == 'ERROR':
                    error_count += 1
    finally:
        con.close()