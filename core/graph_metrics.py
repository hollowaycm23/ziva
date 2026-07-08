import time
import threading
from collections import defaultdict

_node_metrics = defaultdict(lambda: {"count": 0, "total_duration_ms": 0.0, "last_duration_ms": 0.0})
_metrics_lock = threading.Lock()


def track_node(node_name: str):
    def decorator(func):
        def wrapper(state, *args, **kwargs):
            start = time.time()
            try:
                result = func(state, *args, **kwargs)
                return result
            finally:
                elapsed_ms = (time.time() - start) * 1000
                with _metrics_lock:
                    _node_metrics[node_name]["count"] += 1
                    _node_metrics[node_name]["total_duration_ms"] += elapsed_ms
                    _node_metrics[node_name]["last_duration_ms"] = elapsed_ms
        return wrapper
    return decorator


def get_node_metrics():
    with _metrics_lock:
        result = {}
        for name, data in _node_metrics.items():
            avg = data["total_duration_ms"] / data["count"] if data["count"] > 0 else 0
            result[name] = {
                "count": data["count"],
                "total_duration_ms": round(data["total_duration_ms"], 1),
                "avg_duration_ms": round(avg, 1),
                "last_duration_ms": round(data["last_duration_ms"], 1),
            }
        return result


def reset_metrics():
    with _metrics_lock:
        _node_metrics.clear()
