import requests
import base64
from io import BytesIO
from PIL import Image, ImageDraw


def create_test_image():
    """Cria uma imagem simples (Quadrado Vermelho) para testar visão"""
    img = Image.new('RGB', (100, 100), color='white')
    d = ImageDraw.Draw(img)
    d.rectangle([25, 25, 75, 75], fill='red')

    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')


def test_vision():
    url = "http://localhost:8000/chat"

    print("🎨 Criando imagem de teste (Quadrado Vermelho)...")
    img_b64 = create_test_image()

    print("👁️ Enviando para Ziva Vision API...")
    payload = {
        "message": "What is in this image? Describe the color and shape.",
        "images": [img_b64],
        "compact": True
    }

    try:
        # Timeout maior para visão
        resp = requests.post(url, json=payload, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ Resposta da Ziva:\n{data.get('response')}")

            model = data.get('model_used', 'unknown')
            print(f"\nModel Used: {model}")

            response_text = data.get('response', '').lower()
            if "red" in response_text or "square" in response_text or "rectangle" in response_text:
                print("🎉 SUCESSO! A imagem foi correta e visualmente identificada.")
            else:
                print(
                    "⚠️ O modelo respondeu, mas não descreveu corretamente (pode ser alucinação ou modelo errado).")

        else:
            print(f"❌ Erro API ({resp.status_code}): {resp.text}")

    except Exception as e:
        print(f"❌ Falha de conexão: {e}")


if __name__ == "__main__":
    test_vision()
