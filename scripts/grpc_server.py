import grpc
from concurrent import futures
import logging
import os
import sys
from typing import Optional

# Import Protocol Buffers
sys.path.append(os.path.join(os.path.dirname(__file__), '../core/proto'))
import ziva_brain_pb2
import ziva_brain_pb2_grpc

from vllm import LLM, SamplingParams

# Configuration via environment variables
MODEL_NAME = os.getenv('ZIVA_MODEL', 'Qwen/Qwen2.5-14B-Instruct-AWQ')
QUANTIZATION = os.getenv('ZIVA_QUANTIZATION', 'awq')
GPU_MEMORY_UTIL = float(os.getenv('ZIVA_GPU_UTIL', '0.6'))
MAX_MODEL_LEN = int(os.getenv('ZIVA_MAX_MODEL_LEN', '2048'))
LLM_DTYPE = os.getenv('ZIVA_DTYPE', 'float16')
LM_STUDIO_BASE_URL = os.getenv('LM_STUDIO_BASE_URL', 'http://localhost:1234/v1')
LM_STUDIO_API_KEY = os.getenv('LM_STUDIO_API_KEY', 'lm-studio')
LM_STUDIO_MODEL = os.getenv('LM_STUDIO_MODEL', 'batiai/qwen3.6-35b:iq3')
TIMEOUT_SECONDS = int(os.getenv('ZIVA_TIMEOUT', '120'))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BrainServicer(ziva_brain_pb2_grpc.BrainServiceServicer):
    """Servicer for the Ziva Brain gRPC service, handling text generation requests."""

    def __init__(self):
        """Initialize the BrainServicer with LLM configuration."""
        logger.info("🧠 Initializing Ziva Brain Server...")
        self.use_fallback = False
        self.llm: Optional[LLM] = None
        self.client = None
        self._initialize_llm()

    def _initialize_llm(self):
        """Initialize the LLM engine, using vLLM if possible, otherwise fallback to LM Studio."""
        try:
            logger.info("   👉 Attempting Native vLLM (CUDA)...")
            self.llm = LLM(
                model=MODEL_NAME,
                quantization=QUANTIZATION,
                gpu_memory_utilization=GPU_MEMORY_UTIL,
                max_model_len=MAX_MODEL_LEN,
                dtype=LLM_DTYPE,
                trust_remote_code=True
            )
            logger.info("   ✅ Native Engine Ready!")
        except Exception as e:
            logger.warning(f"   ⚠️ Native Engine Failed ({e})")
            logger.info("   👉 Fallback to LM Studio Bridge (HTTP)...")
            self.use_fallback = True
            import openai
            self.client = openai.OpenAI(
                base_url=LM_STUDIO_BASE_URL,
                api_key=LM_STUDIO_API_KEY
            )

    def _validate_request(self, request):
        """Validate the incoming GenerateRequest parameters."""
        if not request.prompt or not request.prompt.strip():
            raise ValueError("Prompt cannot be empty")
        if request.temperature < 0.0 or request.temperature > 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        if request.max_tokens <= 0:
            raise ValueError("Max tokens must be greater than 0")

    def Generate(self, request, context):
        """Generate text based on the provided prompt using the configured LLM."""
        try:
            self._validate_request(request)
            logger.info(f"📥 [gRPC] Received Request ({len(request.prompt)} chars)")

            if self.use_fallback:
                # LM Studio Bridge
                stop = list(request.stop_sequences) if request.stop_sequences else None
                response = self.client.chat.completions.create(
                    model=LM_STUDIO_MODEL,
                    messages=[{"role": "user", "content": request.prompt}],
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    stop=stop,
                    timeout=TIMEOUT_SECONDS
                )
                text = response.choices[0].message.content
                usage = response.usage.total_tokens
                return ziva_brain_pb2.GenerateResponse(text=text, token_usage=usage, finished=True)

            else:
                # Native vLLM
                sampling_params = SamplingParams(
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    stop=list(request.stop_sequences) if request.stop_sequences else None,
                    timeout=TIMEOUT_SECONDS
                )
                outputs = self.llm.generate([request.prompt], sampling_params)
                generated_text = outputs[0].outputs[0].text
                usage = len(outputs[0].outputs[0].token_ids)
                return ziva_brain_pb2.GenerateResponse(text=generated_text, token_usage=usage, finished=True)

        except ValueError as ve:
            logger.error(f"Invalid request: {ve}")
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(ve))
        except Exception as e:
            logger.error(f"Internal error: {e}")
            context.abort(grpc.StatusCode.INTERNAL, f"Generation failed: {e}")

def serve():
    """Start the gRPC server for the BrainService."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    ziva_brain_pb2_grpc.add_BrainServiceServicer_to_server(BrainServicer(), server)
    server.add_insecure_port('[::]:50051')
    logger.info("🚀 Ziva Brain (gRPC+vLLM) listening on port 50051")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
