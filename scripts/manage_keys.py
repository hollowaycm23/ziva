#!/usr/bin/env python3
import sys
import os
import secrets
import json
import hashlib
import argparse

# Include project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SECRETS_FILE = "secrets.json"


def load_secrets():
    if not os.path.exists(SECRETS_FILE):
        return {"api_keys": {}, "users": {"admin": "admin"}}
    with open(SECRETS_FILE, "r") as f:
        return json.load(f)


def save_secrets(data):
    with open(SECRETS_FILE, "w") as f:
        json.dump(data, f, indent=4)


def hash_key(key):
    return hashlib.sha256(key.encode()).hexdigest()


def create_key(name):
    data = load_secrets()
    if name in data["api_keys"]:
        print(f"❌ Key '{name}' already exists.")
        return

    raw_key = secrets.token_urlsafe(32)
    hashed = hash_key(raw_key)

    data["api_keys"][name] = hashed
    save_secrets(data)

    print(f"✅ Key Created!")
    print(f"Name: {name}")
    print(f"Key: {raw_key}")
    print("⚠️  SAVE THIS KEY! It cannot be retrieved later.")


def list_keys():
    data = load_secrets()
    print("🔑 Active API Keys:")
    for name in data["api_keys"]:
        print(f" - {name}")

    print("\n👤 Dashboard Users:")
    for user in data["users"]:
        print(f" - {user}")


def revoke_key(name):
    data = load_secrets()
    if name in data["api_keys"]:
        del data["api_keys"][name]
        save_secrets(data)
        print(f"🗑️ Key '{name}' revoked.")
    else:
        print(f"❌ Key '{name}' not found.")


def set_password(user, password):
    data = load_secrets()
    data["users"][user] = password
    save_secrets(data)
    print(f"✅ Password set for user '{user}'.")


def main():
    parser = argparse.ArgumentParser(description="Ziva Security Manager")
    subparsers = parser.add_subparsers(dest="command")

    # Create
    p_create = subparsers.add_parser("create", help="Create a new API key")
    p_create.add_argument("name", help="Name of the key owner")

    # List
    subparsers.add_parser("list", help="List all keys")

    # Revoke
    p_revoke = subparsers.add_parser("revoke", help="Revoke an API key")
    p_revoke.add_argument("name", help="Name of the key to revoke")

    # Password
    p_pass = subparsers.add_parser("passwd", help="Set dashboard password")
    p_pass.add_argument("user", help="Username")
    p_pass.add_argument("password", help="New Password")

    args = parser.parse_args()

    if args.command == "create":
        create_key(args.name)
    elif args.command == "list":
        list_keys()
    elif args.command == "revoke":
        revoke_key(args.name)
    elif args.command == "passwd":
        set_password(args.user, args.password)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
