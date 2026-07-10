import sqlite3
import os

base_dir = os.path.dirname(__file__)
dbs = [
    os.path.join(base_dir, 'app', 'sql_app.db'),
    os.path.join(base_dir, 'storage', 'dossiers.db'),
]

for db_path in dbs:
    print(f"\n=== Checking {db_path} ===")
    if not os.path.exists(db_path):
        print("  File not found, skipping.")
        continue
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in c.fetchall()]
    print(f"  Tables: {tables}")
    if 'dossiers' in tables:
        c.execute("UPDATE dossiers SET status='a_verifier' WHERE status='incoherent'")
        conn.commit()
        print(f"  Updated records: {c.rowcount}")
        c.execute("SELECT id, status FROM dossiers")
        for row in c.fetchall():
            print(f"    id={row[0]}, status={row[1]}")
    conn.close()
