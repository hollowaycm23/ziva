import grpc
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../core/proto'))
import ziva_brain_pb2
import ziva_brain_pb2_grpc

import time

def run():
    print("🔌 Connecting to Ziva Brain via gRPC (Binary Protocol)...")
    # Connect to localhost:50051
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = ziva_brain_pb2_grpc.BrainServiceStub(channel)
        
        prompt = "Hello, who are you?"
        print(f"🧠 Sending Prompt: '{prompt}'")
        
        start_time = time.time()
        
        request = ziva_brain_pb2.GenerateRequest(
            prompt=prompt,
            temperature=0.7,
            max_tokens=60, # Small generation for ping test
            stop_sequences=[]
        )
        
        try:
            response = stub.Generate(request)
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"✅ Received Binary Response in {duration:.4f}s")
            print(f"📄 Text: {response.text}")
            print(f"🔢 Tokens Used: {response.token_usage}")
            
            if duration > 10.0:
                print("⚠️ WARNING: Slow Response (Likely GPU/Inference bottleneck)")
            else:
                print("🚀 SPEED: Normal for 14B Model")
                 
        except grpc.RpcError as e:
            print(f"🔴 gRPC Error: {e.details()}")

if __name__ == '__main__':
    run()
