
from core.reflection import ReflectionManager
import json

def test_reflection():
    reflector = ReflectionManager()
    
    q = "What is the capital of France?"
    ctx = ["Paris is the capital of France."]
    ans = "The capital of France is Paris."
    
    print("Testing Reflection Manager...")
    result = reflector.reflect(q, ctx, ans)
    print(json.dumps(result, indent=2))
    
    print("Testing Persistence...")
    reflector.save_reflection(result, q, ans)
    
    assert result['score'] >= 4
    assert result['success'] == True

if __name__ == "__main__":
    test_reflection()
