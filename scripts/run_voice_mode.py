from core.voice import VoiceHandler
import sys
import os
import requests
import argparse

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


API_URL = "http://localhost:8000/chat"


def chat_with_ziva(text):
    try:
        payload = {"message": text, "compact": True}
        resp = requests.post(API_URL, json=payload, timeout=30)
        if resp.status_code == 200:
            return resp.json().get("response", "Erro na resposta da API.")
        return f"Erro API: {resp.status_code}"
    except Exception as e:
        return f"Erro de conexão: {e}"


def main():
    parser = argparse.ArgumentParser(description="Ziva Voice Mode")
    parser.add_argument(
        "--test-tts",
        action="store_true",
        help="Teste apenas o TTS")
    args = parser.parse_args()

    print("🎤 Inicializando Ziva Voice Mode...")
    print("⏳ Carregando modelos (pode demorar)...")

    # Init Voice
    voice = VoiceHandler(model_size="base")

    if args.test_tts:
        print("🔊 Testando síntese de voz...")
        voice.speak("System initialized. Voice module online.", lang="en")
        print("✅ Teste concluído.")
        return

    print("\n🟢 ZIVA VOICE ONLINE")
    print("Fale 'sair' ou 'exit' para encerrar.")
    print("-" * 30)

    while True:
        # 1. Ouvir
        user_text = voice.listen()

        if not user_text:
            continue

        print(f"👤 Você: {user_text}")

        if user_text.lower() in ["sair", "exit", "stop", "pare"]:
            voice.speak("Closing voice session. Goodbye.")
            break

        # 2. Pensar (API)
        print("🤖 Ziva: (Pensando...)")
        response_text = chat_with_ziva(user_text)
        print(f"🤖 Ziva: {response_text}")

        # 3. Falar
        voice.speak(response_text)


if __name__ == "__main__":
    main()
