
import sys
import os
import asyncio

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.agent.graph import build_agent
from langchain_core.messages import HumanMessage

async def main():
    if len(sys.argv) < 2:
        print("Usage: python ask_ziva_cli.py 'Your question here'")
        sys.exit(1)

    question = sys.argv[1]
    
    print(f"🤖 Ziva is thinking about: '{question}'...")
    
    # Build the agent
    app = build_agent()
    
    # Create the input state matching AgentState definition
    inputs = {
        "question": question,
        "documents": [],
        "generation": "",
        "chat_history": [],
        "mode": "general"
    }
    
    # Run the agent
    response = await app.ainvoke(inputs)
    
    print("\n🟣 ZIVA SAYS:")
    print("-" * 50)
    # The output of ainvoke on the graph will be the final state
    print(response.get("generation", "No response generated."))
    print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
