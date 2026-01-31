
import sys
import os

# Add root to path
sys.path.append(os.getcwd())

from core.letta_agent import LettaAgentWrapper
import logging

logging.basicConfig(level=logging.INFO)

print("🧪 Testing Letta Connection...")

try:
    letta = LettaAgentWrapper()
    print("WARNING: LettaAgentWrapper initialized.")
    print("If you see this, the client import worked.")
    
    # List agents
    try:
        page = letta.client.agents.list()
        agents = []
        # In SDK 1.x, pages might have internal lists or be iterable
        if hasattr(page, 'items'):
            agents = page.items
        elif hasattr(page, 'data'):
            agents = page.data
        else:
            agents = list(page) # Try direct iteration
             
        print(f"✅ Connection Successful! Found {len(agents)} agents.")
    except Exception as list_e:
        print(f"⚠️ Error listing agents: {list_e}")
        agents = []
    
    # Send Message
    print("Sending message...")
    response = letta.send_message("Hello, can you hear me?")
    print(f"✅ Response received: {response}")

except Exception as e:
    print(f"❌ Letta Test Failure: {e}")
    import traceback
    traceback.print_exc()
