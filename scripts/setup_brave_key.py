#!/usr/bin/env python3
import os
import sys


def setup_brave():
    print("🦁 Brave Search API Setup")
    print("=======================")
    print("To use Brave as your primary search engine (with fallback), you need an API key.")
    print("Get it for FREE at: https://brave.com/search/api/ (2000 queries/month)\n")

    key = input("Paste your Brave API Key (BSA...): ").strip()

    if not key.startswith("BSA"):
        print("⚠️ Warning: Key usually starts with 'BSA'. Double check if this is correct.")
        confirm = input("Continue? [y/N]: ")
        if confirm.lower() != 'y':
            sys.exit(1)

    env_path = os.path.join(os.path.dirname(__file__), '../.env')
    env_path = os.path.abspath(env_path)

    # Read existing env
    lines = []
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()

    # Update or Add key
    new_lines = []
    found = False
    for line in lines:
        if line.startswith("BRAVE_API_KEY="):
            new_lines.append(f"BRAVE_API_KEY={key}\n")
            found = True
        else:
            new_lines.append(line)

    if not found:
        new_lines.append(f"\n# Brave Search\nBRAVE_API_KEY={key}\n")

    # Write back
    with open(env_path, 'w') as f:
        f.writelines(new_lines)

    print(f"\n✅ API Key saved to {env_path}")
    print("🔄 Please restart Ziva for changes to take effect: ./restart.sh")


if __name__ == "__main__":
    setup_brave()
