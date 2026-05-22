import sys
import json
import duckdb
import threading
import time
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich import box
import redis 

r = redis.Redis(decode_responses=True)

con = duckdb.connect("logs.db")

con.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        timestamp TIMESTAMP,
        log_level TEXT,
        message TEXT
    )
""")

THRESHOLD = 3
WINDOW_SECONDS = 10
console = Console()

def replay_from_redis():
    try:
        with open('last_id.txt', 'r') as f:
            last_id = f.read().strip()
    except FileNotFoundError:
        last_id = '0'

    total_replayed = 0
    while True:
        entries = r.xrange('logs', min=f"({last_id}", count=100)
        if not entries:
            break
        for entry_id, fields in entries:
            timestamp = fields.get('timestamp')
            level = fields.get('level', 'UNKNOWN')
            message = fields.get('message', '')
            con.execute("INSERT INTO logs VALUES (CAST(? AS TIMESTAMP), ?, ?)",
                        [timestamp, level, message])
            last_id = entry_id
            with open('last_id.txt', 'w') as f:
                f.write(last_id)
            total_replayed += 1

    if total_replayed > 0:
        console.print(f"[yellow]Replayed {total_replayed} missed entries from Redis[/]")

def check_errors(live):
    con_checker = duckdb.connect("logs.db")
    while True:
        try:
            time.sleep(WINDOW_SECONDS)

            count = con_checker.execute(f"""
                SELECT COUNT(*) FROM logs
                WHERE log_level = 'ERROR'
                AND timestamp > now() - INTERVAL {WINDOW_SECONDS} SECONDS
            """).fetchone()[0]

            total = con_checker.execute("""
                SELECT COUNT(*) FROM logs
            """).fetchone()[0]

            recent_logs = con_checker.execute("""
                SELECT timestamp, log_level, message
                FROM logs
                ORDER BY timestamp DESC
                LIMIT 5
            """).fetchall()

            status = "ALERT" if count >= THRESHOLD else "OK"

            table = Table(box=box.SIMPLE, title=f"STATUS: {status} | ERRORS: {count} in last {WINDOW_SECONDS}s | TOTAL: {total}")
            table.add_column("Timestamp", style="cyan")
            table.add_column("Level", style="white")
            table.add_column("Message", style="white")

            for log in recent_logs:
                level_style = "red" if log[1] == "ERROR" else "green"
                table.add_row(str(log[0]), f"[{level_style}]{log[1]}[/{level_style}]", log[2])

            live.update(table)
        except Exception as e:
            console.print(f"[red]checker error: {e}[/]")

replay_from_redis()

last_id = None
entries_since_flush = 0

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

            timestamp = entry.get('timestamp')
            level = entry.get('level', 'UNKNOWN')
            message = entry.get('message', '')

            con.execute("INSERT INTO logs VALUES (CAST(? AS TIMESTAMP), ?, ?)",
                        [timestamp, level, message])

            try:
                entry_id = r.xadd('logs', {
                    'timestamp': timestamp,
                    'level': level,
                    'message': message
                })
                last_id = entry_id
                entries_since_flush += 1
                if entries_since_flush >= 100:
                    with open('last_id.txt', 'w') as f:
                        f.write(last_id)
                    entries_since_flush = 0
            except redis.RedisError as e:
                console.print(f"[yellow]Redis unavailable, skipping durability: {e}[/]")

    finally:
        if last_id:
            with open('last_id.txt', 'w') as f:
                f.write(last_id)
        con.close()