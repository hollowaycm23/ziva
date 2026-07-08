import sqlite3, os

os.system("docker cp ziva-openwebui:/app/backend/data/webui.db D:\\Stark\\webui_verify.db")

conn = sqlite3.connect(r"D:\Stark\webui_verify.db")
cursor = conn.cursor()

cursor.execute("SELECT key, value FROM config WHERE key LIKE 'ollama%' OR key LIKE 'openai%'")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

conn.close()
os.remove(r"D:\Stark\webui_verify.db")
