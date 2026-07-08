import sqlite3, os

os.system("docker cp ziva-openwebui:/app/backend/data/webui.db D:\\Stark\\webui_apikeys.db")

conn = sqlite3.connect(r"D:\Stark\webui_apikeys.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM api_key")
for row in cursor.fetchall():
    print(f"API Key: {row}")

cursor.execute("SELECT * FROM auth")
for row in cursor.fetchall():
    print(f"Auth: {row}")

cursor.execute("SELECT * FROM user WHERE email='admin@localhost'")
for row in cursor.fetchall():
    print(f"Admin user: {row}")

# Try to check other relevant tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for t in tables:
    name = t[0]
    cursor.execute(f"PRAGMA table_info('{name}')")
    cols = cursor.fetchall()
    col_names = [c[1] for c in cols]
    if 'token' in col_names or 'key' in col_names or 'password' in col_names:
        cursor.execute(f"SELECT * FROM '{name}' LIMIT 3")
        rows = cursor.fetchall()
        if rows:
            print(f"\nTable {name} ({col_names}):")
            for row in rows:
                print(f"  {row}")

conn.close()
os.remove(r"D:\Stark\webui_apikeys.db")
