import sqlite3, os

os.system("docker cp ziva-openwebui:/app/backend/data/webui.db D:\\Stark\\webui_user_fix.db")

conn = sqlite3.connect(r"D:\Stark\webui_user_fix.db")
cursor = conn.cursor()

# Check if any user exists
cursor.execute("SELECT id, name, role FROM user LIMIT 5")
users = cursor.fetchall()
print(f"Existing users: {users}")

# Enable signup in config so user can create first account
cursor.execute(
    "UPDATE config SET value = ? WHERE key = ?",
    ('true', 'enable_signup')
)
print(f"enable_signup: {cursor.rowcount}")

conn.commit()
conn.close()

os.system("docker cp D:\\Stark\\webui_user_fix.db ziva-openwebui:/app/backend/data/webui.db")
os.remove(r"D:\Stark\webui_user_fix.db")
print("Done! Restarting...")
os.system("docker restart ziva-openwebui")
