import sqlite3, os

def inspect(path):
    print("DB:", path)
    if not os.path.exists(path):
        print("  -> não existe\n")
        return
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    print("  tables:", tables)
    if "usuarios" in tables:
        cur.execute("SELECT COUNT(*) FROM usuarios")
        print("  usuarios count:", cur.fetchone()[0])
        cur.execute("SELECT id, display_name, username FROM usuarios LIMIT 5")
        for r in cur.fetchall():
            print("   ", r)
    conn.close()
    print()

base = os.path.join("database", "acaiteria.db")
alt = os.path.join("database", "db.sqlite3")
inspect(base)
inspect(alt)