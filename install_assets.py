import requests
import os
import tarfile


def download_file(url, dest_path):
    print(f"Downloading {url} to {dest_path}...")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    print("Download complete.")


def install_llama_bin():
    os.makedirs("/home/holloway/ziva/bin", exist_ok=True)
    # Fetch latest release URL dynamically
    try:
        api_url = "https://api.github.com/repos/ggml-org/llama.cpp/releases/latest"
        assets = requests.get(api_url).json().get('assets', [])
        # Look for ubuntu-x64
        dl_url = next((a['browser_download_url']
                      for a in assets if 'ubuntu-x64.tar' in a['name']), None)
        if not dl_url:
            print("Could not find ubuntu-x64 asset.")
            return

        tar_path = "/home/holloway/ziva/llama.tar.gz"
        download_file(dl_url, tar_path)

        # Extract
        print("Extracting...")
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(path="/home/holloway/ziva/bin")

        # Move bin/build/bin/llama-server to bin/llama-server if structure is nested
        # Checking structure
        for root, dirs, files in os.walk("/home/holloway/ziva/bin"):
            if "llama-server" in files:
                src = os.path.join(root, "llama-server")
                dst = "/home/holloway/ziva/bin/llama-server"
                if src != dst:
                    os.rename(src, dst)
                    os.chmod(dst, 0o755)
                    print(f"Moved {src} to {dst}")
                break

    except Exception as e:
        print(f"Error installing llama bin: {e}")


def download_model():
    os.makedirs("/home/holloway/ziva/models", exist_ok=True)
    model_url = "https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/resolve/main/qwen2.5-coder-7b-instruct-q4_k_m.gguf"
    dest = "/home/holloway/ziva/models/model.gguf"
    if not os.path.exists(dest):
        download_file(model_url, dest)
    else:
        print("Model already exists.")


if __name__ == "__main__":
    install_llama_bin()
    download_model()
