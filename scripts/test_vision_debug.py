import requests


def test_debug():
    url = "http://localhost:8000/chat"

    # Dummy One-Pixel-ish base64 (not valid image, should cause error in
    # vision handler but prove routing)
    img_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="

    print("👁️ Enviando Dummy Image para Ziva Vision API...")
    payload = {
        "message": "Debug vision",
        "images": [img_b64],
        "compact": True
    }

    try:
        resp = requests.post(url, json=payload, timeout=120)
        print(f"Status Code: {resp.status_code}")
        print(f"Response: {resp.text}")
    except Exception as e:
        print(f"❌ Falha de conexão: {e}")


if __name__ == "__main__":
    test_debug()
