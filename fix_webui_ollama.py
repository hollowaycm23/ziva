import sqlite3, os

os.system("docker cp ziva-openwebui:/app/backend/data/webui.db D:\\Stark\\webui_fix.db")

conn = sqlite3.connect(r"D:\Stark\webui_fix.db")
cursor = conn.cursor()

# Update Ollama base URL to use host.docker.internal
cursor.execute(
    "UPDATE config SET value = ? WHERE key = ?",
    ('["http://host.docker.internal:11434"]', 'ollama.base_urls')
)
print(f"Updated {cursor.rowcount} row(s) for ollama.base_urls")

# Also ensure Ollama is enabled
cursor.execute(
    "UPDATE config SET value = ? WHERE key = ?",
    ('true', 'ollama.enable')
)
print(f"Updated {cursor.rowcount} row(s) for ollama.enable")

conn.commit()
conn.close()

# Copy back to container
os.system("docker cp D:\\Stark\\webui_fix.db ziva-openwebui:/app/backend/data/webui.db")
os.remove(r"D:\Stark\webui_fix.db")
print("Done! Restarting container...")
os.system("docker restart ziva-openwebui")
