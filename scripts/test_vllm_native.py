from vllm import LLM, SamplingParams

# Test minimal vLLM engine loading
try:
    print("🚀 Initializing vLLM Engine directly...")
    llm = LLM(
        model="Qwen/Qwen2.5-14B-Instruct-AWQ",
        quantization="awq",
        gpu_memory_utilization=0.9,
        max_model_len=2048,
        trust_remote_code=True,
        dtype="float16"
    )
    print("✅ Engine Initialized!")
    
    prompts = ["Hello, my name is"]
    sampling_params = SamplingParams(temperature=0.8, top_p=0.95)

    outputs = llm.generate(prompts, sampling_params)
    for output in outputs:
        prompt = output.prompt
        generated_text = output.outputs[0].text
        print(f"Prompt: {prompt!r}, Generated text: {generated_text!r}")

except Exception as e:
    print(f"🔴 CRASH: {e}")
    import traceback
    traceback.print_exc()
