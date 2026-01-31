from core.task_classifier import TaskClassifier
import sys
import os

# Path setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def debug():
    clf = TaskClassifier()
    query = "If I have 5 apples, eat 2, and buy 3 more, how many do I have? Explain the logic step by step."

    print(f"Query: {query}")
    print("-" * 20)

    query_lower = query.lower()
    scores = {}

    for category, rules in clf.categories.items():
        score = 0
        print(f"\nCategory: {category}")

        # Keywords
        matched_kw = []
        for keyword in rules['keywords']:
            if keyword in query_lower:
                score += 1
                matched_kw.append(keyword)
        print(f"  Matched Keywords (+1): {matched_kw}")

        # Patterns
        import re
        matched_pt = []
        for pattern in rules['patterns']:
            if re.search(pattern, query_lower):
                score += 2
                matched_pt.append(pattern)
        print(f"  Matched Patterns (+2): {matched_pt}")

        scores[category] = score
        print(f"  Total Score: {score}")

    best = max(scores, key=scores.get)
    print("\n" + "=" * 20)
    print(f"Final Classification: {best}")


if __name__ == "__main__":
    debug()
