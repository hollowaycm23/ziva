import sqlite3, os

os.system("docker cp ziva-openwebui:/app/backend/data/webui.db D:\\Stark\\webui_reset.db")

conn = sqlite3.connect(r"D:\Stark\webui_reset.db")
cursor = conn.cursor()

# Pre-generated bcrypt hash for "admin123"
new_hash = "$2b$12$fzZoTiU6cSb5PUM9hITiN.2P0DdHywJ0Fh8h/Wl0bnKhBrVOtLAua"

# Update the admin user's password
cursor.execute("UPDATE auth SET password = ? WHERE id IN (SELECT id FROM user WHERE role='admin' LIMIT 1)", (new_hash,))
print(f"Updated admin password: {cursor.rowcount} row(s)")

# Delete pending users
cursor.execute("DELETE FROM user WHERE role='pending'")
print(f"Deleted pending users: {cursor.rowcount}")
cursor.execute("DELETE FROM auth WHERE id NOT IN (SELECT id FROM user)")
print(f"Cleaned orphaned auth: {cursor.rowcount}")

conn.commit()
conn.close()

os.system("docker cp D:\\Stark\\webui_reset.db ziva-openwebui:/app/backend/data/webui.db")
os.remove(r"D:\Stark\webui_reset.db")
print("Done! Restarting...")
os.system("docker restart ziva-openwebui")
