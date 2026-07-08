import sqlite3, os, sys

# Copy webui.db from container to host first
os.system("docker cp ziva-openwebui:/app/backend/data/webui.db D:\\Stark\\webui_check.db")

conn = sqlite3.connect(r"D:\Stark\webui_check.db")
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", [t[0] for t in tables])

for table in tables:
    name = table[0]
    try:
        cursor.execute(f'SELECT * FROM "{name}" LIMIT 10')
        rows = cursor.fetchall()
        col_names = [d[0] for d in cursor.description]
        for row in rows:
            row_str = str(row).lower()
            if any(kw in row_str for kw in ['ollama', 'openai', 'model', 'url', 'base_url', 'connection']):
                print(f'\nTable: {name}')
                print(f'  Columns: {col_names}')
                print(f'  Data: {row}')
    except Exception as e:
        pass

conn.close()
os.remove(r"D:\Stark\webui_check.db")
