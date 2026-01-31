import os
import sys
import sqlite3

def check_peers():
    print("🌍 Ziva P2P Network Status")
    print("=" * 60)
    
import os
import sys
import sqlite3
import time

def check_peers():
    print("🌍 Ziva P2P Network Status")
    print("=" * 60)
    
    db_path = "data/ziva.db" # Correct Path
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check Peers Table
        try:
            cursor.execute("SELECT node_id, trust_level, last_seen FROM peers")
            peers = cursor.fetchall()
            
            if peers:
                print(f"📡 Trusted Peers: {len(peers)}")
                print(f"{'Node ID':<20} {'Trust':<10} {'Last Seen':<20}")
                print("-" * 60)
                for p in peers:
                    last_seen_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(p[2]))
                    print(f"{p[0]:<20} {p[1]:<10} {last_seen_str:<20}")
            else:
                print("⚠️ No trusted peers found in 'peers' table.")
                
        except sqlite3.OperationalError as e:
            print(f"⚠️ Error accessing 'peers' table: {e}")

        # Check Messages Table (Sync Log)
        try:
            cursor.execute("SELECT timestamp, sender, direction, status FROM messages ORDER BY timestamp DESC LIMIT 5")
            logs = cursor.fetchall()
            
            if logs:
                print("\n📝 Recent Message Sychronization:")
                print(f"{'Timestamp':<20} {'Sender':<15} {'Dir':<10} {'Status':<10}")
                print("-" * 60)
                for l in logs:
                    ts_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(l[0]))
                    print(f"{ts_str:<20} {l[1]:<15} {l[2]:<10} {l[3]:<10}")
            else:
                print("\nℹ️ No message logs found.")

        except sqlite3.OperationalError:
            print("ℹ️ 'messages' table not found.")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    check_peers()
