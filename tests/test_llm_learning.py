#!/usr/bin/env python3
"""
Test script for LLM Learning improvements.

Verifies:
1. Enhanced quality scoring
2. Diversity sampling
3. Task classification for new categories
4. Learning scheduler functionality
"""

import json
from core.learning_scheduler import LearningScheduler
from core.training_data_collector import TrainingDataCollector
import sys
sys.path.insert(0, '/home/holloway/ziva')


def test_quality_scoring():
    """Test enhanced quality scoring"""
    print("\n=== Test 1: Quality Scoring ===")
    collector = TrainingDataCollector()

    # Good example
    good_score = collector._calculate_quality(
        instruction="qual o clima em São Paulo",
        tool_call='{"tool": "get_weather", "args": {"location": "São Paulo"}}',
        full_response="A temperatura em São Paulo é de 25°C com céu parcialmente nublado.")

    # Bad example (error in response)
    bad_score = collector._calculate_quality(
        instruction="qual o clima",
        tool_call='{"tool": "get_weather"}',
        full_response="Erro: localização não especificada"
    )

    print(f"✅ Good example score: {good_score:.2f}")
    print(f"❌ Bad example score: {bad_score:.2f}")
    assert good_score > bad_score, "Quality scoring not working correctly"
    print("✅ Quality scoring test passed!")


def test_task_classification():
    """Test new task classifications"""
    print("\n=== Test 2: Task Classification ===")
    collector = TrainingDataCollector()

    test_cases = [
        ('{"tool": "web_search", "args": {"query": "anime"}}',
         "qual anime tem kpop", "web-search"),
        ('{"tool": "get_weather", "args": {"location": "SP"}}',
         "clima em SP", "weather-data"),
        ('{"tool": "local_shell", "args": {"cmd": "ls"}}',
         "listar arquivos", "shell"),
        ('{"tool": "search_documentation", "args": {"q": "python"}}',
         "buscar docs python", "knowledge-retrieval"),
    ]

    for tool_call, instruction, expected in test_cases:
        result = collector._classify_task(instruction, tool_call)
        status = "✅" if result == expected else "❌"
        print(
            f"{status} {instruction[:30]:30} -> {result:20} (expected: {expected})")
        assert result == expected, f"Classification failed for {instruction}"

    print("✅ Task classification test passed!")


def test_diversity_sampling():
    """Test diversity sampling"""
    print("\n=== Test 3: Diversity Sampling ===")
    collector = TrainingDataCollector()

    dataset = collector.get_diverse_dataset(target_size=50, min_quality=0.8)

    # Count task types
    type_counts = {}
    for example in dataset:
        task_type = example['task_type']
        type_counts[task_type] = type_counts.get(task_type, 0) + 1

    print(f"📊 Dataset size: {len(dataset)} examples")
    print(f"📊 Task type distribution:")
    for task_type, count in sorted(type_counts.items()):
        print(f"   {task_type:25} {count:3} examples")

    # Verify diversity (no single type should dominate >60%)
    max_percentage = max(type_counts.values()) / len(dataset) if dataset else 0
    print(f"\n📊 Max type percentage: {max_percentage * 100:.1f}%")
    assert max_percentage < 0.6, "Dataset not diverse enough"
    print("✅ Diversity sampling test passed!")


def test_scheduler_stats():
    """Test scheduler statistics"""
    print("\n=== Test 4: Learning Scheduler ===")
    scheduler = LearningScheduler(
        collection_interval=21600,  # 6 hours
        training_threshold=50,
        min_quality=0.8
    )

    stats = scheduler.get_stats()
    print(f"📊 Scheduler stats:")
    print(json.dumps(stats, indent=2))

    print(f"\n✅ Scheduler initialized successfully!")
    print(
        f"   Collection interval: {
            scheduler.collection_interval /
            3600:.1f} hours")
    print(f"   Training threshold: {scheduler.training_threshold} examples")
    print(f"   New examples available: {stats['new_examples_available']}")


if __name__ == "__main__":
    print("🧪 Testing LLM Learning Improvements")
    print("=" * 60)

    try:
        test_quality_scoring()
        test_task_classification()
        test_diversity_sampling()
        test_scheduler_stats()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
