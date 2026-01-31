#!/usr/bin/env python3
"""
Bootstrap Script - Instala Ziva Worker Node em máquina remota via SSH
"""
import argparse
import subprocess
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def run_ssh(host, command, key_file=None):
    """Executa comando via SSH"""
    ssh_cmd = ["ssh"]
    if key_file:
        ssh_cmd += ["-i", key_file]
    ssh_cmd += ["-o", "StrictHostKeyChecking=no", host, command]

    result = subprocess.run(ssh_cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr


def run_scp(host, local_path, remote_path, key_file=None):
    """Copia arquivo via SCP"""
    scp_cmd = ["scp"]
    if key_file:
        scp_cmd += ["-i", key_file]
    scp_cmd += ["-o", "StrictHostKeyChecking=no",
                "-r", local_path, f"{host}:{remote_path}"]

    result = subprocess.run(scp_cmd, capture_output=True, text=True)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Bootstrap Ziva Worker Node")
    parser.add_argument("--host", required=True, help="SSH target (user@ip)")
    parser.add_argument("--name", required=True, help="Node name (ex: mita)")
    parser.add_argument("--key", help="SSH key file path")
    args = parser.parse_args()

    print(f"🚀 Bootstrapping Ziva Worker: {args.name} @ {args.host}")

    # 1. Test SSH connectivity
    print("🔍 Testing SSH connection...")
    success, out, err = run_ssh(args.host, "echo 'Connected'", args.key)
    if not success:
        print(f"❌ SSH failed: {err}")
        sys.exit(1)
    print("✅ SSH connection OK")

    # 2. Check Python
    print("🐍 Checking Python version...")
    success, out, err = run_ssh(args.host, "python3 --version", args.key)
    if not success:
        print("❌ Python3 not found on remote host")
        sys.exit(1)
    print(f"✅ {out.strip()}")

    # 3. Check Ollama
    print("🦙 Checking Ollama installation...")
    success, out, err = run_ssh(args.host, "which ollama", args.key)
    if not success:
        print("⚠️  Ollama not found. Node will need Ollama installed separately.")
        print("   Install with: curl -fsSL https://ollama.com/install.sh | sh")
    else:
        print(f"✅ Ollama found: {out.strip()}")

    # 4. Create remote directory
    print("📂 Creating remote directory...")
    remote_dir = f"/home/{
        args.host.split('@')[1] if '@' in args.host else 'ubuntu'}/ziva_worker"
    run_ssh(args.host, f"mkdir -p {remote_dir}", args.key)

    # 4. Transfer essential files
    print("📦 Transferring Ziva core files...")
    files_to_transfer = [
        ("core/", f"{remote_dir}/"),
        ("config/node_minimal.json", f"{remote_dir}/config/"),
        ("config/requirements_minimal.txt", f"{remote_dir}/"),
        ("scripts/start_worker.py", f"{remote_dir}/scripts/")
    ]

    for local, remote in files_to_transfer:
        # Create remote subdirs
        remote_subdir = os.path.dirname(remote)
        run_ssh(args.host, f"mkdir -p {remote_subdir}", args.key)

        local_full = PROJECT_ROOT / local
        if not local_full.exists():
            print(f"⚠️  Skipping {local} (not found locally)")
            continue

        print(f"   → {local}")
        if not run_scp(args.host, str(local_full), remote, args.key):
            print(f"❌ Failed to transfer {local}")

    # 5. Update node config with specific name
    print(f"⚙️  Configuring node as '{args.name}'...")
    update_cmd = f"""cd {remote_dir} && python3 -c "
import json
with open('config/node_minimal.json', 'r') as f: cfg = json.load(f)
cfg['node_name'] = '{args.name}'
with open('config/node_minimal.json', 'w') as f: json.dump(cfg, f, indent=2)
"
"""
    run_ssh(args.host, update_cmd, args.key)

    # 6. Install Python dependencies
    print("📚 Installing Python packages...")
    run_ssh(
        args.host,
        f"cd {remote_dir} && pip3 install -r requirements_minimal.txt --user -q",
        args.key)

    # 7. Start worker (in background with nohup)
    print("🚀 Starting worker node...")
    start_cmd = f"cd {remote_dir} && nohup python3 scripts/start_worker.py > worker.log 2>&1 &"
    run_ssh(args.host, start_cmd, args.key)

    print(f"\n✅ Bootstrap complete!")
    print(f"   Node Name: {args.name}")
    print(f"   Remote Dir: {remote_dir}")
    print(f"   Log: {remote_dir}/worker.log")
    print(
        f"\n💡 To check status: ssh {
            args.host} 'tail -f {remote_dir}/worker.log'")


if __name__ == "__main__":
    main()
