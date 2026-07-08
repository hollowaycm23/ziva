import sqlite3, os

os.system("docker cp ziva-openwebui:/app/backend/data/webui.db D:\\Stark\\webui_check2.db")

conn = sqlite3.connect(r"D:\Stark\webui_check2.db")
cursor = conn.cursor()

cursor.execute("SELECT id, name, email, role FROM user")
users = cursor.fetchall()
print(f"Users: {len(users)}")
for u in users:
    print(f"  id={u[0]}, name={u[1]}, email={u[2]}, role={u[3]}")

# Check config
cursor.execute("SELECT key, value FROM config WHERE key IN ('enable_signup','openai.enable','ollama.enable','auth.enable')")
for row in cursor.fetchall():
    print(f"  Config: {row[0]} = {row[1]}")

conn.close()
os.remove(r"D:\Stark\webui_check2.db")
