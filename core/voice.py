import logging
import os
import time
import speech_recognition as sr
from gtts import gTTS
import whisper
import warnings
import tempfile
import subprocess

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VoiceHandler")


class VoiceHandler:
    def __init__(self, model_size="base"):
        """
        Inicializa o VoiceHandler.
        Carrega o modelo Whisper em memória (pode demorar um pouco).
        """
        logger.info(f"🎤 Carregando modelo Whisper ({model_size})...")
        try:
            self.whisper_model = whisper.load_model(model_size)
            logger.info("✅ Modelo Whisper carregado.")
        except Exception as e:
            logger.error(f"❌ Falha ao carregar Whisper: {e}")
            self.whisper_model = None

        self.recognizer = sr.Recognizer()

        # Ajuste de sensibilidade
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True

    def listen(self, timeout=5, phrase_time_limit=10) -> str:
        """
        Ouve o microfone e retorna o texto transcrito.
        """
        if not self.whisper_model:
            return "Erro: Modelo de voz não carregado."

        try:
            with sr.Microphone() as source:
                logger.info("🎧 Ouvindo... (Fale agora)")
                # Ajuste de ruído ambiente rápido
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)

                audio = self.recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_time_limit)

                logger.info("🔄 Processando áudio/transcrevendo...")

                # Salvar temporariamente para o Whisper processar
                # SpeechRecognition pode usar whisper API, mas aqui usamos o modelo local direto
                # Precisamos salvar o áudio raw em wav
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    f.write(audio.get_wav_data())
                    temp_wav = f.name

                # Transcrever com Whisper Local
                # fp16=False para CPU compatibility if needed
                result = self.whisper_model.transcribe(temp_wav, fp16=False)
                text = result["text"].strip()

                # Limpeza
                os.remove(temp_wav)

                logger.info(f"🗣️ Você disse: '{text}'")
                return text

        except sr.WaitTimeoutError:
            logger.info("⏳ Timeout: Nenhuma fala detectada.")
            return ""
        except OSError as e:
            logger.error(f"❌ Erro de Microfone: {e}")
            return "Erro: Microfone não detectado ou inacessível."
        except Exception as e:
            logger.error(f"❌ Erro na escuta: {e}")
            return ""

    def speak(self, text: str, lang="en"):
        """
        Converte texto em áudio e reproduz.
        """
        if not text:
            return

        logger.info(f"🔊 Falando: '{text[:50]}...'")
        try:
            # Gerar MP3 com gTTS
            tts = gTTS(text=text, lang=lang, slow=False)

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                temp_mp3 = f.name

            tts.save(temp_mp3)

            # Reproduzir (ffplay -nodisp -autoexit -loglevel quiet)
            subprocess.run(["ffplay", "-nodisp", "-autoexit",
                            "-loglevel", "quiet", temp_mp3], check=True)

            os.remove(temp_mp3)

        except Exception as e:
            logger.error(f"❌ Erro ao falar: {e}")

# Singleton if needed
# _voice = VoiceHandler()
