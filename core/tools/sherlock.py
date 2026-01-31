import subprocess
import os
import re


class SherlockClient:
    def __init__(self, base_path="/home/holloway/ziva/research/sherlock"):
        self.base_path = base_path
        self.script_path = os.path.join(
            base_path, "sherlock_project", "sherlock.py")

        if not os.path.exists(self.script_path):
            raise FileNotFoundError(
                f"Sherlock script not found at {self.script_path}.")

    def search(self, username: str):
        """
        Executes sherlock for a given username and returns found sites.
        """
        if not re.match(r"^[a-zA-Z0-9_-]+$", username):
            return {"error": "Invalid username format."}

        cmd = [
            "python3", "-m", "sherlock_project", "--timeout", "5",
            "--print-found", "--no-color", username
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.base_path,
                capture_output=True,
                text=True,
                check=False
            )

            output = result.stdout
            found_sites = []
            for line in output.splitlines():
                if "[+]" in line:
                    parts = line.split(": ")
                    if len(parts) >= 2:
                        site_name = parts[0].replace("[+]", "").strip()
                        url = parts[1].strip()
                        found_sites.append({"site": site_name, "url": url})
            return {
                "username": username,
                "found_count": len(found_sites),
                "sites": found_sites,
                "raw_output": output[:500] + "..." if len(output) > 500 else output
            }

        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    client = SherlockClient()
    print(client.search("holloway"))
