import sqlite3, os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')
conn = sqlite3.connect(db_path)
cur  = conn.cursor()

migrations = [
    ("study_plan", "description", "ALTER TABLE study_plan ADD COLUMN description VARCHAR(300) DEFAULT ''"),
    ("day",        "date",        "ALTER TABLE day ADD COLUMN date DATE"),
    ("day",        "completed_at","ALTER TABLE day ADD COLUMN completed_at DATETIME"),
]

for table, col, sql in migrations:
    cur.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cur.fetchall()]
    if col not in cols:
        cur.execute(sql)
        print(f"Added {table}.{col}")
    else:
        print(f"Skip {table}.{col} already exists")

cur.execute("""
    CREATE TABLE IF NOT EXISTS activity (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        message    VARCHAR(300) NOT NULL,
        plan_title VARCHAR(200) NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")
print("activity table ready")

conn.commit()
conn.close()
print("Migration complete. Run: py app.py")
